import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:Krimou1998@localhost/gym_argente'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BOOTSTRAP_SERVE_LOCAL = True