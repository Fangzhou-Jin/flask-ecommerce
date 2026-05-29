"""Tag schemas."""

from marshmallow import Schema, fields, validate


class TagSchema(Schema):
    """Tag read/write schema."""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
