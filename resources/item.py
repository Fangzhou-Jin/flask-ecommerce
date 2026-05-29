"""Item resources: CRUD API with merchant store scoping."""

from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort

from db import db
from models.item import ItemModel
from models.store import StoreModel
from schemas.item import ItemCreateSchema, ItemSchema, ItemUpdateSchema
from utils.authz import (
    assert_item_in_merchant_store,
    get_merchant_store,
    require_merchant,
)

blp = Blueprint(
    "items",
    __name__,
    url_prefix="/items",
    description="Item management",
)


def _get_item_or_404(item_id: int) -> ItemModel:
    return ItemModel.query.get_or_404(item_id)


@blp.route("")
class ItemList(MethodView):
    """GET /items — list; POST /items — create (merchant JWT required)."""

    @blp.response(200, ItemSchema(many=True))
    def get(self):
        return ItemModel.query.all()

    @jwt_required()
    @blp.arguments(ItemCreateSchema)
    @blp.response(201, ItemSchema)
    def post(self, item_data):
        merchant = require_merchant()
        store = get_merchant_store(merchant)
        if not store:
            abort(404, message="Create a store before adding items.")

        if item_data["store_id"] != store.id:
            abort(403, message="You can only add items to your own store.")

        item = ItemModel(**item_data)
        db.session.add(item)
        db.session.commit()
        return item


@blp.route("/mine")
class MyItems(MethodView):
    """GET /items/mine — items in the merchant's store."""

    @jwt_required()
    @blp.response(200, ItemSchema(many=True))
    def get(self):
        merchant = require_merchant()
        store = get_merchant_store(merchant)
        if not store:
            return []
        return ItemModel.query.filter_by(store_id=store.id).all()


@blp.route("/<int:item_id>")
class ItemDetail(MethodView):
    """GET/PUT/DELETE /items/<id>."""

    @blp.response(200, ItemSchema)
    def get(self, item_id):
        return _get_item_or_404(item_id)

    @jwt_required()
    @blp.arguments(ItemUpdateSchema)
    @blp.response(200, ItemSchema)
    def put(self, item_data, item_id):
        merchant = require_merchant()
        item = _get_item_or_404(item_id)
        assert_item_in_merchant_store(item, merchant)

        if "store_id" in item_data and item_data["store_id"] != item.store_id:
            abort(403, message="You cannot move items to another store.")

        if "name" in item_data:
            item.name = item_data["name"]

        if "price" in item_data:
            item.price = item_data["price"]

        db.session.commit()
        return item

    @jwt_required()
    @blp.response(200, ItemSchema)
    def delete(self, item_id):
        merchant = require_merchant()
        item = _get_item_or_404(item_id)
        assert_item_in_merchant_store(item, merchant)
        db.session.delete(item)
        db.session.commit()
        return item
