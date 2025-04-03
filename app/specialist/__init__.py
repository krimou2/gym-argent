from flask import Blueprint

bp = Blueprint('specialist', __name__)

from app.specialist import routes