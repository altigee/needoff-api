SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:1234@127.0.0.1:3347/pyweb'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = 'some-secret-string'
JWT_SECRET_KEY = 'jwt-secret-string'
JWT_BLACKLIST_ENABLED = True
JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
