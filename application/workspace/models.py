from application.shared.database import db, Base
from sqlalchemy import Column, Integer, String, ForeignKey
import uuid


class WorkspaceModel(Base):
    __tablename__ = 'workspace'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    invitation_token = Column(String(255), nullable=False)

    def save_to_db(self):
        db.add(self)
        db.commit()

    @classmethod
    def find_by_name(cls, name):
        return db.query(cls).filter_by(name=name).first()

    @staticmethod
    def generate_invitation_token_string():
        return str(uuid.uuid4())


class WorkspaceUserModel(Base):
    __tablename__ = 'workspace_user'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    ws_id = Column(Integer, ForeignKey('workspace.id'), primary_key=True)

    # TODO: consider adding roles here.

    def save_to_db(self):
        db.add(self)
        db.commit()
