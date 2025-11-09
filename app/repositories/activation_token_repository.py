from sqlalchemy.orm import Session

from app.models.models import ActivationToken


def save_activation_token(db: Session, token: ActivationToken) -> ActivationToken:
    db.add(token)
    db.commit()

    return token

def get_activation_token(db: Session, token_str: str, token_purpose: str) -> ActivationToken | None:
    return db.query(ActivationToken).filter_by(token=token_str, token_purpose=token_purpose).first()

def delete_activation_token(db: Session, token: ActivationToken) -> ActivationToken | None:
    db.delete(token)
    db.commit()