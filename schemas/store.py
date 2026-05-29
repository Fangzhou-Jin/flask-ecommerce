"""Store schemas."""

from marshmallow import Schema, fields, validate


class StoreSchema(Schema):
    """Store response schema."""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    owner_id = fields.Int(dump_only=True)


class StoreCreateSchema(Schema):
    """Store creation request body."""

    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))


class StoreUpdateSchema(Schema):
    """Store update schema (name only)."""

    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
