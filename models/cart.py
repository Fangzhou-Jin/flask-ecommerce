"""
Cart models: one cart per user, line items reference products.
"""

from db import db


class CartModel(db.Model):
    """Shopping cart belonging to a single user."""

    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    user = db.relationship("UserModel", back_populates="cart")
    items = db.relationship(
        "CartItemModel",
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    @property
    def total_price(self) -> float:
        return sum(
            (line.item.price * line.quantity for line in self.items if line.item),
            start=0.0,
        )

    @property
    def total_quantity(self) -> int:
        return sum(line.quantity for line in self.items)

    def __repr__(self) -> str:
        return f"<Cart user={self.user_id}>"


class CartItemModel(db.Model):
    """Single product line inside a cart."""

    __tablename__ = "cart_items"
    __table_args__ = (
        db.UniqueConstraint("cart_id", "item_id", name="uq_cart_item"),
    )

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(
        db.Integer,
        db.ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id = db.Column(
        db.Integer,
        db.ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity = db.Column(db.Integer, nullable=False, default=1)

    cart = db.relationship("CartModel", back_populates="items")
    item = db.relationship("ItemModel", lazy="joined")

    @property
    def subtotal(self) -> float:
        if self.item:
            return round(self.item.price * self.quantity, 2)
        return 0.0

    def __repr__(self) -> str:
        return f"<CartItem item={self.item_id} qty={self.quantity}>"
