"""
Item model and many-to-many association table items_tags (ItemTag).

Item belongs to one Store; Item and Tag have a many-to-many relationship.
"""

from db import db

items_tags = db.Table(
    "items_tags",
    db.Column(
        "item_id",
        db.Integer,
        db.ForeignKey("items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "tag_id",
        db.Integer,
        db.ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class ItemModel(db.Model):
    """Product entity belonging to a store."""

    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float(precision=2), nullable=False)
    store_id = db.Column(
        db.Integer,
        db.ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    store = db.relationship("StoreModel", back_populates="items")

    tags = db.relationship(
        "TagModel",
        secondary=items_tags,
        back_populates="items",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<Item {self.name}>"
