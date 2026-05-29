"""Authorization helpers for role-based access control."""

from flask_jwt_extended import get_jwt_identity
from flask_smorest import abort

from models.item import ItemModel
from models.store import StoreModel
from models.user import UserModel
from utils.constants import ROLE_CUSTOMER, ROLE_MERCHANT


def get_current_user_id() -> int:
    return int(get_jwt_identity())


def get_current_user() -> UserModel:
    user = UserModel.query.get(get_current_user_id())
    if not user:
        abort(401, message="User not found.")
    return user


def require_customer() -> UserModel:
    user = get_current_user()
    if user.role != ROLE_CUSTOMER:
        abort(403, message="Only customer accounts can use the shopping cart.")
    return user


def require_merchant() -> UserModel:
    user = get_current_user()
    if user.role != ROLE_MERCHANT:
        abort(403, message="Only merchant accounts can perform this action.")
    return user


def get_merchant_store(user: UserModel) -> StoreModel | None:
    return StoreModel.query.filter_by(owner_id=user.id).first()


def require_merchant_store(user: UserModel) -> StoreModel:
    store = get_merchant_store(user)
    if not store:
        abort(404, message="You do not have a store yet.")
    return store


def assert_store_owner(store: StoreModel, user: UserModel) -> None:
    if store.owner_id != user.id:
        abort(403, message="You can only manage your own store.")


def assert_item_in_merchant_store(item: ItemModel, user: UserModel) -> None:
    store = get_merchant_store(user)
    if not store or item.store_id != store.id:
        abort(403, message="You can only manage items in your own store.")
