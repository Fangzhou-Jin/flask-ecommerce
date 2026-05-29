"""Cart schemas."""

from marshmallow import Schema, fields, validate


class ItemBriefSchema(Schema):
    """Product snapshot nested in cart line items."""

    id = fields.Int(dump_only=True)
    name = fields.Str()
    price = fields.Float()
    store_id = fields.Int()


class CartItemSchema(Schema):
    """Cart line item with nested product info."""

    id = fields.Int(dump_only=True)
    item_id = fields.Int(dump_only=True)
    quantity = fields.Int()
    subtotal = fields.Float(dump_only=True)
    item = fields.Nested(ItemBriefSchema, dump_only=True)


class CartSchema(Schema):
    """Full cart response."""

    id = fields.Int(dump_only=True)
    items = fields.List(fields.Nested(CartItemSchema), dump_only=True)
    total_price = fields.Float(dump_only=True)
    total_quantity = fields.Int(dump_only=True)


class AddCartItemSchema(Schema):
    """Add product to cart."""

    item_id = fields.Int(required=True)
    quantity = fields.Int(load_default=1, validate=validate.Range(min=1))


class UpdateCartItemSchema(Schema):
    """Update line item quantity."""

    quantity = fields.Int(required=True, validate=validate.Range(min=1))
