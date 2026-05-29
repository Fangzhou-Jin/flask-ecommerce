"""
Extensions module: register third-party Flask extensions.

Initialized via init_app in the application factory for easy test overrides.
"""

from flask_jwt_extended import JWTManager
from flask_smorest import Api

jwt = JWTManager()
api = Api()
