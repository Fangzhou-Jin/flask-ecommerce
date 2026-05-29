"""User model for JWT registration and login."""

from db import db
from utils.constants import ROLE_CUSTOMER


class UserModel(db.Model):
    """System user with hashed password and role."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_CUSTOMER, index=True)

    cart = db.relationship(
        "CartModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    stores = db.relationship(
        "StoreModel",
        back_populates="owner",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
