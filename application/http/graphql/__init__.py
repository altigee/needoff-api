from flask import Blueprint
from flask_graphql import GraphQLView
import application.http.graphql.schema as sch
from flask_jwt_extended import jwt_required
import logging

LOG = logging.getLogger('[graphql]')

graphql_resolver = Blueprint('graphql', __name__)


def init_graphql(jwt_enabled, dump_schema_enabled=True):
    schema = sch.create_schema(dump_schema_enabled)

    graphql_view = GraphQLView.as_view(name='graphql', schema=schema, graphiql=True)
    if jwt_enabled:
        graphql_resolver.add_url_rule('/graphql', view_func=jwt_required(graphql_view))
    else:
        graphql_resolver.add_url_rule('/graphql', view_func=graphql_view)
