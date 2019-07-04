from graphene_sqlalchemy import SQLAlchemyObjectType
import graphene

from application.auth.models import User as UserModel
from application.balances.models import DayOff as DayOffModel
from application.users.models import UserProfile as ProfileModel
from application.workspace.models import (
    WorkspaceModel,
    WorkspaceInvitation as WorkspaceInvitationModel,
    WorkspaceDate as WorkspaceDateModel,
    WorkspaceUser as WorkspaceUserModel
)
from application.rules.models import execute_balance_calculation_rule


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
    balance = graphene.Field(lambda: Balance)

    class Meta:
        model = WorkspaceUserModel

    def resolve_balance(self, _):
        rule_result = execute_balance_calculation_rule(ws_id=1, user_id=self.user_id)

        return Balance(
            left_paid_leaves=rule_result.left_paid_leaves,
            left_unpaid_leaves=rule_result.left_unpaid_leaves,
            left_sick_leaves=rule_result.left_sick_leaves,
            total_paid_leaves=rule_result.total_paid_leaves,
            total_unpaid_leaves=rule_result.total_unpaid_leaves,
            total_sick_leaves=rule_result.total_sick_leaves
        )


class WorkspaceInvitation(SQLAlchemyObjectType):
    class Meta:
        model = WorkspaceInvitationModel


class WorkspaceDate(SQLAlchemyObjectType):
    class Meta:
        model = WorkspaceDateModel
