"""Item schemas."""

from marshmallow import Schema, fields, validate


class TagBriefSchema(Schema):
    """Brief tag info nested in item responses."""

    id = fields.Int(dump_only=True)
    name = fields.Str()


class ItemSchema(Schema):
    """Full item schema including tags."""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    store_id = fields.Int(required=True)
    tags = fields.List(fields.Nested(TagBriefSchema), dump_only=True)


class ItemCreateSchema(Schema):
    """Item creation request body."""

    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    store_id = fields.Int(required=True)


class ItemUpdateSchema(Schema):
    """Item update request body (all fields optional)."""

    name = fields.Str(validate=validate.Length(min=1, max=80))
    price = fields.Float(validate=validate.Range(min=0))
    store_id = fields.Int()
