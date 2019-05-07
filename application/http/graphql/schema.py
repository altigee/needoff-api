from application.http.graphql import types
from application.http.graphql.mutations import *
from graphene_sqlalchemy import SQLAlchemyConnectionField
from graphene import relay


class Query(graphene.ObjectType):
    node = relay.Node.Field()
    all_users = SQLAlchemyConnectionField(types.UserConnections)
    all_days_off = SQLAlchemyConnectionField(types.DayOffConnections)


class Mutation(graphene.ObjectType):
    create_day_off = CreateDayOff.Field()


schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    types=[
        types.DayOff,
        types.User
    ]
)
