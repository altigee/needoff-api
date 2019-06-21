import datetime
from application.shared.database import db, Base, Persistent
import uuid
from enum import Enum, auto
import pickle
from intellect.Intellect import Intellect


class WorkspaceInvitationStatus(Enum):
    ACCEPTED = 0
    PENDING = 1
    REVOKED = 2


class WorkspaceUserRoles(Enum):
    MEMBER = auto()
    APPROVER = auto()
    ADMIN = auto()
    OWNER = auto()

    @classmethod
    def is_valid_role(cls, role):
        return role in cls.__members__


class WorkspaceRuleTypes(Enum):
    BALANCE_CALCULATION = auto()
    DAY_OFF_VALIDATION = auto()


class WorkspaceModel(Base, Persistent):
    __tablename__ = 'workspace'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.String(255))
    invitation_link_token = db.Column(db.String(255))

    @staticmethod
    def generate_invitation_link_token():
        return str(uuid.uuid4())

    @classmethod
    def find_by_user_id(cls, user_id):
        ws_ids = [x.ws_id for x in WorkspaceUser.find_all(user_id=user_id)]
        return cls.query().filter(WorkspaceModel.id.in_(ws_ids))


class WorkspaceUser(Base, Persistent):
    __tablename__ = 'workspace_user'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    ws_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), primary_key=True)
    start_date = db.Column(db.Date, default=datetime.datetime.now(), nullable=False)

    def get_worked_months(self):
        now = datetime.datetime.now()
        return (now.year - self.start_date.year) * 12 + now.month - self.start_date.month


class WorkspaceInvitation(Base, Persistent):
    __tablename__ = 'workspace_invitation'

    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    ws_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), nullable=False)
    status = db.Column(db.Enum(WorkspaceInvitationStatus), default=WorkspaceInvitationStatus.PENDING, nullable=False)
    start_date = db.Column(db.Date, nullable=True)


class WorkspaceDate(Base, Persistent):
    __tablename__ = 'workspace_date'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    ws_id = db.Column(db.Integer, db.ForeignKey('workspace.id'))
    date = db.Column(db.Date, nullable=False)
    is_official_holiday = db.Column(db.Boolean(), nullable=True)

    @staticmethod
    def get_work_days_count(ws_id, start_date, end_date):
        holidays = WorkspaceDate.query(). \
            filter(WorkspaceDate.date.between(start_date, end_date)). \
            filter(WorkspaceDate.ws_id == ws_id). \
            filter(WorkspaceDate.is_official_holiday is True). \
            all()

        result = 0

        holiday_dates = map(lambda h: h.date, holidays)

        date = start_date

        while date <= end_date:
            if date.weekday() < 5 and date not in holiday_dates:
                result += 1

            date = date + datetime.timedelta(days=1)

        return result

class WorkspaceUserRole(Base, Persistent):
    __tablename__ = 'workspace_user_role'

    ws_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, primary_key=True)
    role = db.Column(db.Enum(WorkspaceUserRoles), default=WorkspaceUserRoles.MEMBER, nullable=False, primary_key=True)


class WorkspaceRule(Base, Persistent):
    __tablename__ = 'workspace_rule'

    ws_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), nullable=False, primary_key=True)
    type = db.Column(db.Enum(WorkspaceRuleTypes), nullable=False, primary_key=True)
    rule = db.Column(db.String, nullable=False)
    node = db.Column(db.BLOB, nullable=True)

    def __init__(self, ws_id, type, rule):
        self.ws_id = ws_id
        self.type = type
        self.rule = rule
        self.node = pickle.dumps(Intellect().learn_policy(rule))
