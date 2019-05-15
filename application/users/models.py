from application.shared.database import db, Base, Persistent

class UserProfile(Base, Persistent):
    __tablename__ = 'user_profile'

    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True, nullable=False)
    first_name = db.Column('first_name', db.String, nullable=False)
    last_name = db.Column('last_name', db.String, nullable=False)
    position = db.Column('position', db.String, nullable=False)
    phone = db.Column('phone', db.String, nullable=False)
    email = db.Column('email', db.String, nullable=False)
    user = db.relationship('User', foreign_keys=[user_id])

    @classmethod
    def find_by_user_id(cls, user_id):
        return cls.query().filter_by(user_id=user_id).first()
