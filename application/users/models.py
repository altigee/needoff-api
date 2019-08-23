from application.shared.database import db, Base, Persistent

class UserProfile(Base, Persistent):
    __tablename__ = 'user_profile'

    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True, nullable=False)
    first_name = db.Column('first_name', db.String, nullable=True)
    last_name = db.Column('last_name', db.String, nullable=True)
    position = db.Column('position', db.String, nullable=True)
    phone = db.Column('phone', db.String, nullable=True)
    email = db.Column('email', db.String, nullable=False)
    user = db.relationship('User', foreign_keys=[user_id])

    @classmethod
    def find_by_user_id(cls, user_id):
        return cls.find(user_id=user_id)

class UserDevice(Base, Persistent):
    __tablename__ = 'user_device'

    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), nullable=False)
    device_token = db.Column('device_token', db.String, primary_key=True, nullable=False)