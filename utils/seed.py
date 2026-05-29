"""Insert dummy data when the database is empty."""

from db import db
from models.item import ItemModel, items_tags
from models.store import StoreModel
from models.tag import TagModel
from models.user import UserModel
from utils.constants import ROLE_CUSTOMER, ROLE_MERCHANT
from utils.security import hash_password


def load_dummy_data():
    """Add sample data on first run (skips if stores already exist)."""
    if StoreModel.query.first():
        return

    demo = UserModel(
        username="demo",
        password=hash_password("demo1234"),
        role=ROLE_CUSTOMER,
    )
    merchant = UserModel(
        username="merchant",
        password=hash_password("merchant1234"),
        role=ROLE_MERCHANT,
    )
    merchant2 = UserModel(
        username="merchant2",
        password=hash_password("merchant1234"),
        role=ROLE_MERCHANT,
    )
    merchant3 = UserModel(
        username="merchant3",
        password=hash_password("merchant1234"),
        role=ROLE_MERCHANT,
    )
    db.session.add_all([demo, merchant, merchant2, merchant3])
    db.session.flush()

    tech = StoreModel(name="Tech Store", owner_id=merchant.id)
    fashion = StoreModel(name="Fashion Hub", owner_id=merchant2.id)
    books = StoreModel(name="Book Corner", owner_id=merchant3.id)
    db.session.add_all([tech, fashion, books])
    db.session.flush()

    tag_electronics = TagModel(name="electronics")
    tag_sale = TagModel(name="sale")
    tag_new = TagModel(name="new")
    tag_clothing = TagModel(name="clothing")
    tag_books = TagModel(name="books")
    db.session.add_all([tag_electronics, tag_sale, tag_new, tag_clothing, tag_books])
    db.session.flush()

    item_list = [
        ItemModel(name="Laptop", price=999.99, store_id=tech.id),
        ItemModel(name="Wireless Mouse", price=29.99, store_id=tech.id),
        ItemModel(name="Mechanical Keyboard", price=89.99, store_id=tech.id),
        ItemModel(name="Cotton T-Shirt", price=19.99, store_id=fashion.id),
        ItemModel(name="Denim Jeans", price=49.99, store_id=fashion.id),
        ItemModel(name="Flask Web Development", price=39.99, store_id=books.id),
        ItemModel(name="Clean Architecture", price=44.99, store_id=books.id),
    ]
    db.session.add_all(item_list)
    db.session.flush()

    links = [
        (item_list[0].id, tag_electronics.id),
        (item_list[0].id, tag_sale.id),
        (item_list[0].id, tag_new.id),
        (item_list[1].id, tag_electronics.id),
        (item_list[1].id, tag_sale.id),
        (item_list[2].id, tag_electronics.id),
        (item_list[2].id, tag_new.id),
        (item_list[3].id, tag_clothing.id),
        (item_list[3].id, tag_sale.id),
        (item_list[4].id, tag_clothing.id),
        (item_list[4].id, tag_new.id),
        (item_list[5].id, tag_books.id),
        (item_list[5].id, tag_sale.id),
        (item_list[6].id, tag_books.id),
        (item_list[6].id, tag_new.id),
    ]
    db.session.execute(items_tags.insert(), [{"item_id": i, "tag_id": t} for i, t in links])

    db.session.commit()
