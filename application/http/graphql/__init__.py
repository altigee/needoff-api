from flask import Blueprint, request
from flask_graphql import GraphQLView
import application.http.graphql.schema as sch
from flask_jwt_extended import jwt_required
import logging

LOG = logging.getLogger('[graphql]')

graphql_resolver = Blueprint('graphql', __name__)


@graphql_resolver.before_request
def before_gql_request():
    print('>> before gql request')
    print(request.path, request.data)
    pass


def init_graphql(jwt_enabled, dump_schema_enabled=True):
    schema = sch.create_schema(dump_schema_enabled)

    graphql_view = GraphQLView.as_view(name='graphql', schema=schema, graphiql=True)
    graphql_resolver.add_url_rule('/graphql', view_func=graphql_view)
