from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.models.models import User

def get_user_by_email(db: Session, email: EmailStr):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, full_name: str, email: EmailStr, password: str):
    user = User(
        full_name=full_name,
        email=str(email),
        password_hash=password
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user