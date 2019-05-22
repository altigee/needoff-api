import datetime
from application.shared.database import db, Base, Persistent
import uuid
from enum import Enum
from sqlalchemy.orm import relationship


class WorkspaceInvitationStatus(Enum):
    ACCEPTED = 0
    PENDING = 1
    REVOKED = 2


class WorkspaceUserRelationTypes(Enum):
    OWNER = 0
    MEMBER = 1


class WorkspaceModel(Base, Persistent):
    __tablename__ = 'workspace'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.String(255))
    invitation_link_token = db.Column(db.String(255))

    @staticmethod
    def generate_invitation_link_token():
        return str(uuid.uuid4())

    @classmethod
    def find_by_user_id(cls, user_id):
        ws_ids = [x.ws_id for x in WorkspaceUserModel.find_all(user_id=user_id)]
        return cls.query().filter(WorkspaceModel.id.in_(ws_ids))


class WorkspaceUserModel(Base, Persistent):
    __tablename__ = 'workspace_user'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    ws_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), primary_key=True)
    relation_type = db.Column(db.Enum(WorkspaceUserRelationTypes), default=WorkspaceUserRelationTypes.MEMBER, nullable=False)
    start_date = db.Column(db.Date, default=datetime.datetime.now(), nullable=False)

    # TODO: consider adding roles here.


class WorkspaceInvitation(Base, Persistent):
    __tablename__ = 'workspace_invitation'

    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    ws_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), nullable=False)
    status = db.Column(db.Enum(WorkspaceInvitationStatus), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
