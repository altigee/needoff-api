from application.shared.database import db, Base, Persistent
import uuid


class WorkspaceModel(Base, Persistent):
    __tablename__ = 'workspace'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    invitation_token = db.Column(db.String(255), nullable=False)

    @classmethod
    def find_by_name(cls, name):
        return cls.query().filter_by(name=name).first()

    @staticmethod
    def generate_invitation_token_string():
        return str(uuid.uuid4())


class WorkspaceUserModel(Base, Persistent):
    __tablename__ = 'workspace_user'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    ws_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), primary_key=True)

    # TODO: consider adding roles here.
