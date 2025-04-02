"""
Characters blueprint initialization
"""
from flask import Blueprint

characters_bp = Blueprint('characters', __name__, url_prefix='/characters')

from app.characters import routes