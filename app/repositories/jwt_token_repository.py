import hashlib
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import User, RefreshToken

def hash_token(token: str) -> str:
    return hashlib.sha1(token.encode('utf-8')).hexdigest()

def save_jwt_token(
        db: Session,
        user: User,
        token: str,
        expires_in_days: int = 7
):
    hashed = hash_token(token)
    expiry_date = datetime.utcnow() + timedelta(days=expires_in_days)

    db_token = RefreshToken(
        hashed_token=hashed,
        user_id=user.id,
        expiry_date=expiry_date,
        is_revoked=False
    )

    db.add(db_token)
    db.commit()
    db.refresh(db_token)

def verify_jwt_token(db: Session, token: str):
    hashed = hash_token(token)
    db_token = db.query(RefreshToken).filter(
        RefreshToken.hashed_token == hashed,
        RefreshToken.is_revoked == False,
    ).first()

    if not db_token or db_token.expiry_date < datetime.utcnow():
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

def revoke_refresh_token(db: Session, token: str):
    hashed = hashlib.sha256(token.encode()).hexdigest()
    db_token = db.query(RefreshToken).filter(
        RefreshToken.hashed_token == hashed,
        RefreshToken.is_revoked == False
    ).first()

    if db_token:
        db_token.is_revoked = True
        db.commit()