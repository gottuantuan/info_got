from redis import StrictRedis
class Config:
    DEBUG = True
    SECRET_KEY = 'TDxS5BoJlW6zUFhOZhTHwu3X2OpVFIHIbZdA+JZAgD1Uz92XMZFJNA=='
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@localhost/info_got'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    SESSION_TYPE = 'redis'
    SESSION_REDIS = StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 86400


class developmentConfig(Config):
    DEBUG = True


class productionConfig(Config):
    DEBUG = False


config = {
    'develop': developmentConfig,
    'production': productionConfig
}