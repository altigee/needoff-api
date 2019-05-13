from graphene_sqlalchemy import SQLAlchemyObjectType
from application.balances.models import DayOff as DayOffModel
from application.auth.models import User as UserModel
from graphene import relay


class User(SQLAlchemyObjectType):
    class Meta:
        model = UserModel
        interfaces = (relay.Node,)
        exclude_fields = ('password',)


class DayOff(SQLAlchemyObjectType):
    class Meta:
        model = DayOffModel
        interfaces = (relay.Node,)
