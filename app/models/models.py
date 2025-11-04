from sqlalchemy import Column, Integer, String, Text, ForeignKey, func
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100))
    email = Column(String(100), unique=True)
    status = Column(String(10))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    password_hash = Column(Text)

    # --- Связи ---
    tokens = relationship("ActivationToken", back_populates="user")

    projects_created = relationship(
        "Project",
        back_populates="creator",
        foreign_keys="Project.created_by"
    )

    # Связь для ProjectMember.user
    memberships = relationship("ProjectMember", back_populates="user")


class ActivationToken(Base):
    __tablename__ = 'activation_tokens'
    id = Column(Integer, primary_key=True)
    token = Column(String(255))
    user_id = Column(Integer, ForeignKey('users.id'))
    expiry_date = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    token_purpose = Column(Text)

    user = relationship("User", back_populates="tokens")

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    description = Column(Text)
    purpose_id = Column(Integer, ForeignKey("project_purposes.id"))

    creator = relationship("User", back_populates="projects_created", foreign_keys=[created_by])
    members = relationship("ProjectMember", back_populates="project")
    purpose = relationship("ProjectPurposes", back_populates="projects")


class ProjectMember(Base):
    __tablename__ = 'project_members'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    role_id = Column(Integer, ForeignKey('roles.id'))
    created_at = Column(TIMESTAMP, server_default=func.now())

    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="memberships")
    role = relationship("Role", back_populates="members")


class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    members = relationship("ProjectMember", back_populates="role")

class ProjectPurposes(Base):
    __tablename__ = 'project_purposes'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), index=True)
    projects = relationship("Project", back_populates="purpose")