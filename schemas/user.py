"""User schemas: register, login, and public user info."""

from marshmallow import Schema, fields, validate

from utils.constants import ROLES


class UserRegisterSchema(Schema):
    """Registration request body."""

    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=128))
    role = fields.Str(
        required=True,
        validate=validate.OneOf(ROLES, error="Role must be 'merchant' or 'customer'."),
    )


class UserLoginSchema(Schema):
    """Login request body."""

    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class UserSchema(Schema):
    """User info returned to clients (no password)."""

    id = fields.Int(dump_only=True)
    username = fields.Str()
    role = fields.Str()


class TokenSchema(Schema):
    """JWT token returned on successful login."""

    access_token = fields.Str()
    token_type = fields.Str()
    user = fields.Nested(UserSchema)
