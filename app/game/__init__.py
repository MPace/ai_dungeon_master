"""
Game blueprint initialization
"""
from flask import Blueprint

game_bp = Blueprint('game', __name__, url_prefix='/game')

from app.game import routes
from app.game import memory_routes