"""Resource layer: register all Flask-Smorest Blueprints."""

from resources.auth import blp as auth_blp
from resources.cart import blp as cart_blp
from resources.item import blp as item_blp
from resources.store import blp as store_blp
from resources.tag import blp as tag_blp


def register_blueprints(api):
    """Register module Blueprints with the Smorest API."""
    api.register_blueprint(auth_blp)
    api.register_blueprint(store_blp)
    api.register_blueprint(item_blp)
    api.register_blueprint(tag_blp)
    api.register_blueprint(cart_blp)
