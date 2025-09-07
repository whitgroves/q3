'''Configuration objects for qqueue to use via Flask.config.from_object().'''

import os
from secrets import token_hex

DATABASE_DIR = os.path.join(os.path.abspath(os.getcwd()), '.database')
SQLITE_PREFIX = 'sqlite:///'

class BaseConfig(): # pylint: disable=too-few-public-methods
    '''Base values for qqueue configuration objects.'''
    SECRET_KEY = str()
    SQLALCHEMY_DATABASE_URI = str()
    SQLALCHEMY_TRACK_MODIFICATIONS = False # https://stackoverflow.com/a/33790196/3178898 pylint: disable=line-too-long
    TESTING = False


class DevConfig(BaseConfig): # pylint: disable=too-few-public-methods
    '''Configuration for dev (local) instances of the app.'''
    SECRET_KEY = os.environ.get('QQ_SECRET_KEY') or \
          'AnEmbarassingPhotoOfSpongeBobAtTheChristmasParty'
    SQLALCHEMY_DATABASE_URI = SQLITE_PREFIX + \
        os.path.join(DATABASE_DIR, 'qqdev.db')


class TestConfig(BaseConfig): # pylint: disable=too-few-public-methods
    '''Configuration for test (local) instances of the app.'''
    SECRET_KEY = os.environ.get('QQ_SECRET_KEY') or token_hex(32)
    SQLALCHEMY_DATABASE_URI = SQLITE_PREFIX + \
         os.path.join(DATABASE_DIR, 'qqtest.db')
    TESTING = True


class ProdConfig(BaseConfig): # pylint: disable=too-few-public-methods
    '''Configuration for deployed (AWS) instances of the app.'''
    SECRET_KEY = os.environ.get('QQ_SECRET_KEY') # or token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('QQ_DATABASE_URI') or \
        SQLITE_PREFIX + os.path.join(DATABASE_DIR, 'qqueue.db')


ACCEPTED_CURRENCIES = ['USD', 'EUR', 'CAD'] + sorted([
    'USDT',
    'BTC',
    'ETH',
    'DAI',
    'USDC',
    'SOL',
    'XRP',
    'BNB',
    'DOGE',
    'LINK',
    'ADA',
    'TRX',
    'CRO',
    'AVAX',
    'LTC',
])
