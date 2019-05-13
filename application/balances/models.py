from application.shared.database import db, Base, Persistent

# TODO refactor to enums? (there were problems with Graphene)
LEAVE_VACATION_PAID = "LEAVE_VACATION_PAID"
LEAVE_VACATION_UNPAID = "LEAVE_VACATION_UNPAID"
LEAVE_SICK_LEAVE = "LEAVE_SICK_LEAVE"
_valid_leaves = [LEAVE_VACATION_PAID, LEAVE_VACATION_UNPAID, LEAVE_SICK_LEAVE]

BALANCE_SICK_LEAVE = "BALANCE_SICK_LEAVE"
BALANCE_VACATION = "BALANCE_VACATION"
_valid_balances = [BALANCE_SICK_LEAVE, BALANCE_VACATION]


def is_valid_leave_type(leave_type):
    return leave_type in _valid_leaves


def is_valid_balance_type(balance_type):
    return balance_type in _valid_balances


class DayOff(Base, Persistent):
    __tablename__ = 'day_off'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', foreign_keys=[user_id])

    approved_by_id = db.Column('approved_by_id', db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])

    leave_type = db.Column('leave_type', db.String(120), nullable=False)


class Balance(Base, Persistent):
    __tablename__ = 'balance'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), nullable=False)
    #user = db.relationship('User', backref='balances', foreign_keys=[user_id])
    balance_type = db.Column('balance_type', db.String(120), nullable=False)
    amount = db.Column('amount', db.Integer, nullable=False)

    @classmethod
    def find_by_user(cls, user_id):
        return cls.query().filter_by(user_id=user_id).all()
