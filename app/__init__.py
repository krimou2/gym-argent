from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
bootstrap = Bootstrap()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    bootstrap.init_app(app)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.specialist import bp as specialist_bp
    app.register_blueprint(specialist_bp, url_prefix='/specialist')

    return app

from app import models