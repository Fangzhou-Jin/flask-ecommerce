"""Cart resources: customer-only shopping cart API."""

from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort

from db import db
from models.cart import CartItemModel, CartModel
from models.item import ItemModel
from schemas.cart import AddCartItemSchema, CartSchema, UpdateCartItemSchema
from utils.authz import get_current_user_id, require_customer

blp = Blueprint(
    "cart",
    __name__,
    url_prefix="/cart",
    description="Shopping cart",
)


def _get_or_create_cart(user_id: int) -> CartModel:
    cart = CartModel.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = CartModel(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return cart


def _serialize_cart(cart: CartModel) -> dict:
    return {
        "id": cart.id,
        "items": [
            {
                "id": line.id,
                "item_id": line.item_id,
                "quantity": line.quantity,
                "subtotal": line.subtotal,
                "item": {
                    "id": line.item.id,
                    "name": line.item.name,
                    "price": line.item.price,
                    "store_id": line.item.store_id,
                }
                if line.item
                else None,
            }
            for line in cart.items
        ],
        "total_price": round(cart.total_price, 2),
        "total_quantity": cart.total_quantity,
    }


def _get_cart_line(cart: CartModel, item_id: int) -> CartItemModel | None:
    return next((line for line in cart.items if line.item_id == item_id), None)


@blp.route("")
class CartResource(MethodView):
    """GET /cart — view cart; DELETE /cart — clear cart."""

    @jwt_required()
    @blp.response(200, CartSchema)
    def get(self):
        require_customer()
        cart = _get_or_create_cart(get_current_user_id())
        return _serialize_cart(cart)

    @jwt_required()
    @blp.response(200, CartSchema)
    def delete(self):
        require_customer()
        cart = _get_or_create_cart(get_current_user_id())
        for line in list(cart.items):
            db.session.delete(line)
        db.session.commit()
        return _serialize_cart(cart)


@blp.route("/items")
class CartItemList(MethodView):
    """POST /cart/items — add or increment item."""

    @jwt_required()
    @blp.arguments(AddCartItemSchema)
    @blp.response(200, CartSchema)
    def post(self, data):
        require_customer()
        item = ItemModel.query.get(data["item_id"])
        if not item:
            abort(404, message="Item not found.")

        cart = _get_or_create_cart(get_current_user_id())
        existing = _get_cart_line(cart, data["item_id"])

        if existing:
            existing.quantity += data["quantity"]
        else:
            db.session.add(
                CartItemModel(
                    cart_id=cart.id,
                    item_id=data["item_id"],
                    quantity=data["quantity"],
                )
            )

        db.session.commit()
        db.session.refresh(cart)
        return _serialize_cart(cart)


@blp.route("/items/<int:item_id>")
class CartItemDetail(MethodView):
    """PUT /cart/items/<id> — update qty; DELETE — remove line."""

    @jwt_required()
    @blp.arguments(UpdateCartItemSchema)
    @blp.response(200, CartSchema)
    def put(self, data, item_id):
        require_customer()
        cart = _get_or_create_cart(get_current_user_id())
        line = _get_cart_line(cart, item_id)
        if not line:
            abort(404, message="Item not in cart.")

        line.quantity = data["quantity"]
        db.session.commit()
        db.session.refresh(cart)
        return _serialize_cart(cart)

    @jwt_required()
    @blp.response(200, CartSchema)
    def delete(self, item_id):
        require_customer()
        cart = _get_or_create_cart(get_current_user_id())
        line = _get_cart_line(cart, item_id)
        if not line:
            abort(404, message="Item not in cart.")

        db.session.delete(line)
        db.session.commit()
        db.session.refresh(cart)
        return _serialize_cart(cart)
