from graphene_sqlalchemy import SQLAlchemyObjectType

from application.auth.models import User as UserModel
from application.balances.models import Balance as BalanceModel
from application.balances.models import DayOff as DayOffModel
from application.users.models import UserProfile as ProfileModel
from application.workspace.models import (
    WorkspaceModel,
    WorkspaceInvitation as WorkspaceInvitationModel,
    WorkspaceHolidayCalendar as WorkspaceHolidayCalendarModel,
    Holiday as HolidayModel
)


class User(SQLAlchemyObjectType):
    class Meta:
        model = UserModel
        exclude_fields = ('password', 'jti')


class DayOff(SQLAlchemyObjectType):
    class Meta:
        model = DayOffModel


class Balance(SQLAlchemyObjectType):
    class Meta:
        model = BalanceModel


class Profile(SQLAlchemyObjectType):
    class Meta:
        model = ProfileModel


class Workspace(SQLAlchemyObjectType):
    class Meta:
        model = WorkspaceModel


class WorkspaceInvitation(SQLAlchemyObjectType):
    class Meta:
        model = WorkspaceInvitationModel


class WorkspaceHolidayCalendar(SQLAlchemyObjectType):
    class Meta:
        model = WorkspaceHolidayCalendarModel


class Holiday(SQLAlchemyObjectType):
    class Meta:
        model = HolidayModel
