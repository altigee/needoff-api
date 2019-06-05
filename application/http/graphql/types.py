from graphene_sqlalchemy import SQLAlchemyObjectType
import graphene

from application.auth.models import User as UserModel
from application.balances.models import DayOff as DayOffModel
from application.users.models import UserProfile as ProfileModel
from application.workspace.models import (
    WorkspaceModel,
    WorkspaceInvitation as WorkspaceInvitationModel,
    WorkspaceHoliday as HolidayModel,
    WorkspaceUser as WorkspaceUserModel
)


class User(SQLAlchemyObjectType):
    class Meta:
        model = UserModel
        exclude_fields = ('password', 'jti')


class DayOff(SQLAlchemyObjectType):
    class Meta:
        model = DayOffModel


class Balance(graphene.ObjectType):
    left_paid_leaves = graphene.Int()
    left_unpaid_leaves = graphene.Int()
    left_sick_leaves = graphene.Int()

    total_paid_leaves = graphene.Int()
    total_unpaid_leaves = graphene.Int()
    total_sick_leaves = graphene.Int()


class Profile(SQLAlchemyObjectType):
    class Meta:
        model = ProfileModel


class Workspace(SQLAlchemyObjectType):
    class Meta:
        model = WorkspaceModel


class WorkspaceUser(SQLAlchemyObjectType):
    class Meta:
        model = WorkspaceUserModel


class WorkspaceInvitation(SQLAlchemyObjectType):
    class Meta:
        model = WorkspaceInvitationModel


class Holiday(SQLAlchemyObjectType):
    class Meta:
        model = HolidayModel
