SQLALCHEMY_DATABASE_URI = 'sqlite:///../db/needoff.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = 'some-secret-string'
JWT_SECRET_KEY = 'jwt-secret-string'
JWT_BLACKLIST_ENABLED = True
JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
GRAPHQL_JWT_ENABLED = True
