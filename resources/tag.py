"""Tag resources: list, create, and link tags to items."""

from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort

from db import db
from models.item import ItemModel
from models.tag import TagModel
from schemas.item import ItemSchema
from schemas.tag import TagSchema
from utils.authz import assert_item_in_merchant_store, require_merchant

blp = Blueprint(
    "tags",
    __name__,
    url_prefix="",
    description="Tag management",
)


@blp.route("/tags")
class TagList(MethodView):
    """GET /tags — list; POST /tags — create (merchant JWT required)."""

    @blp.response(200, TagSchema(many=True))
    def get(self):
        return TagModel.query.all()

    @jwt_required()
    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data):
        require_merchant()

        if TagModel.query.filter_by(name=tag_data["name"]).first():
            abort(409, message="Tag name already exists.")

        tag = TagModel(**tag_data)
        db.session.add(tag)
        db.session.commit()
        return tag


@blp.route("/items/<int:item_id>/tags/<int:tag_id>")
class ItemTagLink(MethodView):
    """POST — link a tag to an item (merchant JWT required)."""

    @jwt_required()
    @blp.response(200, ItemSchema)
    def post(self, item_id, tag_id):
        merchant = require_merchant()
        item = ItemModel.query.get_or_404(item_id)
        assert_item_in_merchant_store(item, merchant)
        tag = TagModel.query.get_or_404(tag_id)

        if tag in item.tags:
            abort(409, message="Tag already linked to this item.")

        item.tags.append(tag)
        db.session.commit()
        return item
