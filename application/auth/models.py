from passlib.hash import pbkdf2_sha256 as sha256
from application.shared.database import db, Base, Persistent


class User(Base, Persistent):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(120), nullable=False)
    created_time = db.Column(db.DateTime(), nullable=False)
    jti = db.Column(db.String, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    @classmethod
    def find_by_username(cls, username):
        return cls.query().filter_by(username=username).first()

    @classmethod
    def find(cls, **kwargs):
        return cls.query().filter_by(**kwargs).first()

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, password_hash):
        return sha256.verify(password, password_hash)
