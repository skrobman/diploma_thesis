from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base, relationship

from app.database import engine

metadata = MetaData()
metadata.reflect(bind=engine)
Base = declarative_base(metadata=metadata)

class User(Base):
    __table__ = metadata.tables['users']
    tokens = relationship("ActivationToken", back_populates="user")

class ActivationToken(Base):
    __table__ = metadata.tables['activation_tokens']
    user = relationship("User", back_populates="tokens")