from flask_jwt_extended import JWTManager

jwt = JWTManager()


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    from application.auth import models
    jti = decrypted_token['jti']
    return models.RevokedToken.is_jti_blacklisted(jti)
