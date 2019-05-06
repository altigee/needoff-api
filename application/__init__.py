from flask import Flask
from application.shared.database import db
from application.jwt import jwt
from application.auth.v1_controller import auth_v1
from application.http.health_controller import health_v1
from application.http import httperrors
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, )
app.config.from_pyfile('../config/default.py')
# needs to be passed in arguments, potentially defined in docker-compose '/instance/dev_config.py'
app.config.from_envvar('APPLICATION_SETTINGS', silent=True)

db.app = app
db.init_app(app)
db.create_all()

jwt.init_app(app)

app.register_blueprint(auth_v1)
app.register_blueprint(health_v1)
app.register_blueprint(httperrors)
