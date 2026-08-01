import secrets

from sqlalchemy.orm import Session

from fitminiapp_api.models.user import User

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_client_code(db: Session) -> str:
    for _ in range(20):
        raw = "".join(secrets.choice(CODE_ALPHABET) for _ in range(7))
        code = f"{raw[:4]}-{raw[4:]}"
        if not db.query(User.id).filter(User.client_code == code).first():
            return code
    raise RuntimeError("Не удалось создать уникальный код клиента")


def ensure_client_code(db: Session, user: User) -> str:
    if not user.client_code:
        user.client_code = generate_client_code(db)
        db.flush()
    return user.client_code


def rotate_client_code(db: Session, user: User) -> str:
    previous = user.client_code
    while True:
        code = generate_client_code(db)
        if code != previous:
            user.client_code = code
            db.commit()
            return code
