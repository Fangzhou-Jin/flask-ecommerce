"""Tag model: many-to-many relationship with Item."""

from db import db


class TagModel(db.Model):
    """Item tag, e.g. electronics, sale."""

    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    items = db.relationship(
        "ItemModel",
        secondary="items_tags",
        back_populates="tags",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"
