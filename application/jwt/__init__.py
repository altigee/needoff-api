from flask_jwt_extended import JWTManager

jwt = JWTManager()

@jwt.user_loader_callback_loader
def logged_id_user_load_callback(identity):
    from application.auth.models import User
    return User.find(email=identity)