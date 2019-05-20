from application.shared.database import db, Base, Persistent
import uuid
from enum import Enum


class WorkspaceInvitationStatus(Enum):
    ACCEPTED = 0
    PENDING = 1
    REVOKED = 2


class WorkspaceModel(Base, Persistent):
    __tablename__ = 'workspace'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    invitation_link_token = db.Column(db.String(255))

    @staticmethod
    def generate_invitation_link_token():
        return str(uuid.uuid4())


class WorkspaceUserModel(Base, Persistent):
    __tablename__ = 'workspace_user'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    ws_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), primary_key=True)
    start_date = db.Column(db.Date, nullable=False)

    # TODO: consider adding roles here.


class WorkspaceInvitation(Base, Persistent):
    __tablename__ = 'workspace_invitation'

    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    ws_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), nullable=False)
    status = db.Column(db.Enum(WorkspaceInvitationStatus), nullable=False)
    start_date = db.Column(db.Date, nullable=True)

    @classmethod
    def list(cls, **kwargs):
        return cls.query().filter_by(**kwargs).all()
