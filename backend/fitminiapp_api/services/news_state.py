from __future__ import annotations

from sqlalchemy.orm import Session

from fitminiapp_api.models.news import NewsCluster, NewsStateTransition


def transition_news_cluster(
    db: Session,
    cluster: NewsCluster,
    to_status: str,
    *,
    reason_code: str,
    actor_ref: str | None = None,
    from_status: str | None = None,
) -> bool:
    previous = from_status or cluster.status
    if previous == to_status:
        return False
    db.add(
        NewsStateTransition(
            cluster_id=cluster.id,
            from_status=previous,
            to_status=to_status,
            reason_code=reason_code,
            actor_ref=actor_ref,
        )
    )
    cluster.status = to_status
    return True
