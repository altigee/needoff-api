from application.shared.database import db, Base
from sqlalchemy import Column, Integer, ForeignKey, Enum as DBEnum
from sqlalchemy.orm import relationship
from enum import Enum


class DayOffType(Enum):
    VACATION_PAID = 0
    VACATION_UNPAID = 1
    SICK_LEAVE = 2


class DayOff(Base):
    __tablename__ = 'day_off'

    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('user.id'), nullable=False)
    user = relationship('User', backref='days_off', foreign_keys=[user_id])

    approved_by_id = Column('approved_by_id', Integer, ForeignKey('user.id'), nullable=True)
    approved_by = relationship('User', foreign_keys=[approved_by_id])

    day_off_type = Column('day_off_type', DBEnum(DayOffType), nullable=False)

    def save_to_db(self):
        db.add(self)
        db.commit()
