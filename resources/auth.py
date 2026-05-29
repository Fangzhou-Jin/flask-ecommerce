"""Authentication resources: user registration and JWT login."""

from flask.views import MethodView
from flask_jwt_extended import create_access_token
from flask_smorest import Blueprint, abort

from db import db
from models.user import UserModel
from schemas.user import TokenSchema, UserLoginSchema, UserRegisterSchema, UserSchema
from utils.security import hash_password, verify_password

blp = Blueprint(
    "auth",
    __name__,
    url_prefix="/",
    description="User authentication: register and login",
)


@blp.route("/register")
class UserRegister(MethodView):
    """POST /register — create a new user."""

    @blp.arguments(UserRegisterSchema)
    @blp.response(201, UserSchema)
    def post(self, user_data):
        username = user_data["username"]
        password = user_data["password"]
        role = user_data["role"]

        if UserModel.query.filter_by(username=username).first():
            abort(409, message="Username already exists.")

        user = UserModel(
            username=username,
            password=hash_password(password),
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        return user


@blp.route("/login")
class UserLogin(MethodView):
    """POST /login — validate credentials and return JWT."""

    @blp.arguments(UserLoginSchema)
    @blp.response(200, TokenSchema)
    def post(self, login_data):
        user = UserModel.query.filter_by(username=login_data["username"]).first()

        if user is None or not verify_password(login_data["password"], user.password):
            abort(401, message="Invalid username or password.")

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role},
        )
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "user": user,
        }
