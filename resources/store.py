"""Store resources: CRUD API with merchant ownership."""

from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort

from db import db
from models.store import StoreModel
from schemas.store import StoreCreateSchema, StoreSchema, StoreUpdateSchema
from utils.authz import (
    assert_store_owner,
    get_merchant_store,
    require_merchant,
)

blp = Blueprint(
    "stores",
    __name__,
    url_prefix="/stores",
    description="Store management",
)


@blp.route("")
class StoreList(MethodView):
    """GET /stores — list; POST /stores — create (merchant JWT required)."""

    @blp.response(200, StoreSchema(many=True))
    def get(self):
        return StoreModel.query.all()

    @jwt_required()
    @blp.arguments(StoreCreateSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        merchant = require_merchant()

        if get_merchant_store(merchant):
            abort(409, message="Merchant already has a store.")

        if StoreModel.query.filter_by(name=store_data["name"]).first():
            abort(409, message="Store name already exists.")

        store = StoreModel(name=store_data["name"], owner_id=merchant.id)
        db.session.add(store)
        db.session.commit()
        return store


@blp.route("/mine")
class MyStore(MethodView):
    """GET /stores/mine — merchant's own store."""

    @jwt_required()
    @blp.response(200, StoreSchema)
    def get(self):
        merchant = require_merchant()
        store = get_merchant_store(merchant)
        if not store:
            abort(404, message="You do not have a store yet.")
        return store


@blp.route("/<int:store_id>")
class StoreDetail(MethodView):
    """GET/PUT/DELETE /stores/<id>."""

    @blp.response(200, StoreSchema)
    def get(self, store_id):
        return StoreModel.query.get_or_404(store_id)

    @jwt_required()
    @blp.arguments(StoreUpdateSchema)
    @blp.response(200, StoreSchema)
    def put(self, store_data, store_id):
        merchant = require_merchant()
        store = StoreModel.query.get_or_404(store_id)
        assert_store_owner(store, merchant)

        existing = StoreModel.query.filter_by(name=store_data["name"]).first()
        if existing and existing.id != store_id:
            abort(409, message="Store name already exists.")

        store.name = store_data["name"]
        db.session.commit()
        return store

    @jwt_required()
    @blp.response(200, StoreSchema)
    def delete(self, store_id):
        merchant = require_merchant()
        store = StoreModel.query.get_or_404(store_id)
        assert_store_owner(store, merchant)
        db.session.delete(store)
        db.session.commit()
        return store
