from application.shared.database import db, Base, Persistent
from enum import Enum, auto

BALANCE_SICK_LEAVE = "BALANCE_SICK_LEAVE"
BALANCE_VACATION = "BALANCE_VACATION"
_valid_balances = [BALANCE_SICK_LEAVE, BALANCE_VACATION]


class LeaveTypes(Enum):
    SICK_LEAVE = auto()
    VACATION_PAID = auto()
    VACATION_UNPAID = auto()
    WFH = auto()


LeaveTypesLabels = {
    'SICK_LEAVE': 'Sick Leave',
    LeaveTypes.SICK_LEAVE: 'Sick Leave',
    'VACATION_PAID': 'Vacation',
    LeaveTypes.VACATION_PAID: 'Vacation',
    'VACATION_UNPAID': 'Day Off',
    LeaveTypes.VACATION_UNPAID: 'Day Off',
    'WFH': 'WFH',
    LeaveTypes.WFH: 'WFH'
}


def is_valid_leave_type(leave_type):
    return leave_type in LeaveTypes.__members__


def is_valid_balance_type(balance_type):
    return balance_type in _valid_balances


class DayOff(Base, Persistent):
    __tablename__ = 'day_off'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user_profile.user_id'), nullable=False)
    user = db.relationship('UserProfile', foreign_keys=[user_id])

    approved_by_id = db.Column('approved_by_id', db.Integer, db.ForeignKey('user_profile.user_id'), nullable=True)
    approved_by = db.relationship('UserProfile', foreign_keys=[approved_by_id])

    leave_type = db.Column('leave_type', db.Enum(LeaveTypes), nullable=False)

    start_date = db.Column('start_date', db.Date, nullable=False)
    end_date = db.Column('end_date', db.Date, nullable=False)

    workspace_id = db.Column('workspace_id', db.Integer, db.ForeignKey('workspace.id'), nullable=False)
    workspace = db.relationship('WorkspaceModel', foreign_keys=[workspace_id])

    comment = db.Column('comment', db.String(255), nullable=True)

    @classmethod
    def find_by_user_id(cls, user_id):
        return cls.find_all(user_id=user_id)


# TODO: Delete it. We don't store balances.
class Balance:
    __tablename__ = 'balance'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), nullable=False)
    # user = db.relationship('User', backref='balances', foreign_keys=[user_id])
    balance_type = db.Column('balance_type', db.String(120), nullable=False)
    amount = db.Column('amount', db.Integer, nullable=False)

    @classmethod
    def find_by_user_id(cls, user_id):
        return cls.find_all(user_id=user_id)
