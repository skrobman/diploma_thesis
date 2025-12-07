from sqlalchemy import Column, Integer, String, Text, ForeignKey, func, Boolean
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    status = Column(String(10), server_default='inactive', nullable=False)
    password_hash = Column(Text, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    projects_created = relationship(
        "Project",
        back_populates="creator",
        foreign_keys="Project.created_by"
    )

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        passive_deletes=True
    )

    memberships = relationship(
        "ProjectMember",
        back_populates="user",
        passive_deletes=True
    )

    activation_tokens = relationship(
        "ActivationToken",
        back_populates="user",
        passive_deletes=True
    )

    invitations = relationship(
        "ProjectInvitationTokens",
        back_populates="user",
        passive_deletes=True
    )


class ActivationToken(Base):
    __tablename__ = 'activation_tokens'
    id = Column(Integer, primary_key=True)
    token = Column(String(255), nullable=False, unique=True)
    # 👇 CASCADE
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    expiry_date = Column(TIMESTAMP, nullable=False)
    token_purpose = Column(Text, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="activation_tokens")


class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'))
    description = Column(Text)
    purpose_id = Column(Integer, ForeignKey("project_purposes.id"))

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    creator = relationship("User", back_populates="projects_created", foreign_keys=[created_by])
    members = relationship("ProjectMember", back_populates="project", passive_deletes=True)
    purpose = relationship("ProjectPurposes", back_populates="projects")
    invitation_tokens = relationship("ProjectInvitationTokens", back_populates="project", passive_deletes=True)

class ProjectMember(Base):
    __tablename__ = 'project_members'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())

    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="memberships")
    role = relationship("Role", back_populates="members")


class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    members = relationship("ProjectMember", back_populates="role")


class ProjectPurposes(Base):
    __tablename__ = 'project_purposes'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), index=True, nullable=False, unique=True)
    projects = relationship("Project", back_populates="purpose")


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    id = Column(Integer, primary_key=True, index=True)
    hashed_token = Column(String, nullable=False, unique=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expiry_date = Column(TIMESTAMP, nullable=False)
    is_revoked = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="refresh_tokens")


class ProjectInvitationTokens(Base):
    __tablename__ = 'project_invitations_tokens'
    id = Column(Integer, primary_key=True)
    hashed_token = Column(String, nullable=False, unique=True)

    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="invitation_tokens")
    user = relationship("User", back_populates="invitations")