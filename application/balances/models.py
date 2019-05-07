from application.shared.database import db
from enum import Enum


class DayOffType(Enum):
    VACATION_PAID = 0
    VACATION_UNPAID = 1
    SICK_LEAVE = 2


class DayOff(db.Model):
    __tablename__ = 'day_off'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='days_off', foreign_keys=[user_id])

    approved_by_id = db.Column('approved_by_id', db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])

    day_off_type = db.Column('day_off_type', db.Enum(DayOffType), nullable=False)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
