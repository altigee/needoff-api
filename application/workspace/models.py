import datetime
from application.shared.database import db, Base, Persistent
import uuid
from enum import Enum


class WorkspaceInvitationStatus(Enum):
    ACCEPTED = 0
    PENDING = 1
    REVOKED = 2


class WorkspaceUserRelationTypes(Enum):
    OWNER = 0
    MEMBER = 1


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
    relation_type = db.Column(db.Enum(WorkspaceUserRelationTypes), default=WorkspaceUserRelationTypes.MEMBER, nullable=False)
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


class WorkspaceHoliday(Base, Persistent):
    __tablename__ = 'workspace_holiday'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    ws_id = db.Column(db.Integer, db.ForeignKey('workspace.id'))
    date = db.Column(db.Date, nullable=False)

    @staticmethod
    def get_work_days_count(ws_id, start_date, end_date):
        holidays = WorkspaceHoliday.query().\
            filter(WorkspaceHoliday.date.between(start_date, end_date)).\
            filter(WorkspaceHoliday.ws_id == ws_id).\
            all()
        result = 0
        holiday_dates = set(map(lambda h: h.date, holidays))

        date = start_date

        while date <= end_date:
            is_holiday = False
            for holiday_date in holiday_dates:
                if date == holiday_date:
                    is_holiday = True
                    break

            if date.weekday() < 5 and not is_holiday:
                result += 1

            date = date + datetime.timedelta(days=1)

        return result


class WorkspacePolicy(Base, Persistent):
    __tablename__ = 'workspace_policy'

    ws_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), nullable=False, primary_key=True)
    max_paid_vacations_per_year = db.Column(db.Integer)
    max_unpaid_vacations_per_year = db.Column(db.Integer)
    max_sick_leaves_per_year = db.Column(db.Integer)
