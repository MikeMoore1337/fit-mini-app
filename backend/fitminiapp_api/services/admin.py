from sqlalchemy.orm import Session

from fitminiapp_api.models.billing import Payment, Subscription
from fitminiapp_api.models.notification import Notification
from fitminiapp_api.models.program import ProgramTemplate
from fitminiapp_api.models.user import User, UserProfile


def admin_users(db: Session) -> list[User]:
    return (
        db.query(User)
        .outerjoin(UserProfile, UserProfile.user_id == User.id)
        .order_by(User.id.desc())
        .all()
    )


def admin_templates(db: Session) -> list[ProgramTemplate]:
    return db.query(ProgramTemplate).order_by(ProgramTemplate.id.desc()).all()


def admin_payments(db: Session) -> list[Payment]:
    return db.query(Payment).order_by(Payment.id.desc()).all()


def admin_subscriptions(db: Session) -> list[Subscription]:
    return db.query(Subscription).order_by(Subscription.id.desc()).all()


def admin_notifications(db: Session) -> list[Notification]:
    return db.query(Notification).order_by(Notification.id.desc()).limit(100).all()
