from sanic import Sanic
from application.shared.database import db
from application.auth.v1_controller import auth_v1
from application.http.health_controller import health_v1
from application.workspace.v1_controller import ws_v1
from application.http import httperrors
import logging
import application.balances.models
import application.http.graphql.resolver as graphql
from application.auth.jwt import *

logging.basicConfig(level=logging.DEBUG)

app = Sanic(__name__, )
app.config.from_pyfile('config/default.py')
# needs to be passed in arguments, potentially defined in docker-compose '/instance/dev_config.py'
# app.config.from_envvar('APPLICATION_SETTINGS')



app.blueprint(auth_v1)
app.blueprint(health_v1)
app.blueprint(ws_v1)
app.blueprint(httperrors)

graphql.init_graphql(
    jwt_enabled=app.config['GRAPHQL_JWT_ENABLED'],
    dump_schema_enabled=app.config['GRAPHQL_SCHEMA_DUMP_ENABLED']
)
app.blueprint(graphql.graphql_resolver)
