from app.api.dependencies.auth import require_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")

    db.delete(notification)
    db.commit()
