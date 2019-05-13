from passlib.hash import pbkdf2_sha256 as sha256
from application.shared.database import db, Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import as_declarative


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(120), unique=True, nullable=False)
    password = Column(String(120), nullable=False)
    refresh_token = Column(String, nullable=True)

    async def save_to_db(self):
        db.add(self)
        db.commit()

    @classmethod
    async def find_by_username(cls, username):
        return db.query(cls).filter(username=username).first()

    @classmethod
    async def find_by_id(cls, user_id):
        return db.query(cls).filter(id=user_id).first()

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, password_hash):
        return sha256.verify(password, password_hash)
