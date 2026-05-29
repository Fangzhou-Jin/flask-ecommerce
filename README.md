# E-Commerce REST API (Flask)

University software architecture project: a modular e-commerce backend API built with **Flask + Flask-Smorest + SQLAlchemy + JWT**.

## Tech Stack

| Technology         | Purpose                                       |
| ------------------ | --------------------------------------------- |
| Python 3           | Runtime                                       |
| Flask              | Web framework                                 |
| Flask-Smorest      | REST API + OpenAPI/Swagger                    |
| Flask-SQLAlchemy   | ORM                                           |
| Flask-JWT-Extended | JWT authentication                            |
| Marshmallow        | Request/response validation and serialization |
| MySQL 8            | Database (via PyMySQL)                        |
| Docker             | Containerized deployment                      |

## Project Structure

```
Flask/
├── app.py                 # Application Factory entry point
├── db.py                  # SQLAlchemy instance
├── models/                # ORM data models
├── schemas/               # Marshmallow schemas
├── resources/             # Flask-Smorest Blueprints (route layer)
├── extensions/            # JWT, Api extensions
├── utils/                 # Password hashing, unified responses
├── templates/             # Frontend HTML
├── static/                # Frontend static assets
├── instance/              # Optional SQLite fallback directory
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
└── README.md
```

## Database Relationships

```
User (standalone, authentication only)

Store 1 ──< * Item
                *
                |
                * (many-to-many via items_tags)
                |
                * Tag
```

- **Store → Item**: one-to-many via `Item.store_id` foreign key.
- **Item ↔ Tag**: many-to-many via association table `items_tags` (`item_id`, `tag_id`).
- **User**: decoupled from business entities; handles register/login only.

## Quick Start

### Local Development

Start MySQL first (easiest via Docker):

```bash
docker compose up mysql -d
```

Then run the API on your machine:

```bash
cd Flask
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask run --port 5001
```

The default `.env` connects to `127.0.0.1:3307` with user `ecommerce` / password `ecommerce123` (port 3307 avoids conflict with local MySQL on 3306).

Visit:

- **Frontend dashboard**: http://127.0.0.1:5001/
- **API health check**: http://127.0.0.1:5001/api/health
- **Swagger docs**: http://127.0.0.1:5001/swagger-ui

### Frontend Features

The web dashboard (`templates/` + `static/`) provides:

- User registration / login (JWT stored in browser localStorage)
- Browse and CRUD for stores, items, and tags (writes require login)
- Many-to-many linking between items and tags
- Full integration with the REST API; no build step required

### Docker (API + MySQL)

```bash
docker compose up --build
```

This starts:

- **MySQL 8** on port `3307` (mapped to container 3306; data persisted in volume `mysql_data`)
- **Flask API** on port `5001`

Build the API image only (requires external MySQL):

```bash
docker build -t ecommerce-api .
docker run -p 5001:5001 --env-file .env ecommerce-api
```

## API Overview

| Method | Path                             | Auth    | Description        |
| ------ | -------------------------------- | ------- | ------------------ |
| POST   | `/register`                      | No      | Register user      |
| POST   | `/login`                         | No      | Login, returns JWT |
| GET    | `/stores`                        | No      | List stores        |
| GET    | `/stores/<id>`                   | No      | Store detail       |
| POST   | `/stores`                        | **JWT** | Create store       |
| PUT    | `/stores/<id>`                   | **JWT** | Update store       |
| DELETE | `/stores/<id>`                   | **JWT** | Delete store       |
| GET    | `/items`                         | No      | List items         |
| GET    | `/items/<id>`                    | No      | Item detail        |
| POST   | `/items`                         | **JWT** | Create item        |
| PUT    | `/items/<id>`                    | **JWT** | Update item        |
| DELETE | `/items/<id>`                    | **JWT** | Delete item        |
| GET    | `/tags`                          | No      | List tags          |
| POST   | `/tags`                          | **JWT** | Create tag         |
| POST   | `/items/<item_id>/tags/<tag_id>` | **JWT** | Link tag to item   |

Protected endpoints require this header:

```
Authorization: Bearer <access_token>
```

## API Examples

### 1. Register

```bash
curl -X POST http://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret12"}'
```

### 2. Login

```bash
curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret12"}'
```

Example response:

```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "user": { "id": 1, "username": "alice" }
}
```

### 3. Create Store (JWT required)

```bash
export TOKEN="eyJ..."   # Replace with access_token from login

curl -X POST http://127.0.0.1:5000/stores \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Tech Store"}'
```

### 4. Create Item

```bash
curl -X POST http://127.0.0.1:5000/items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Laptop", "price": 999.99, "store_id": 1}'
```

### 5. Create Tag and Link to Item

```bash
curl -X POST http://127.0.0.1:5000/tags \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "electronics"}'

curl -X POST http://127.0.0.1:5000/items/1/tags/1 \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Public Queries (no token)

```bash
curl http://127.0.0.1:5000/stores
curl http://127.0.0.1:5000/items
curl http://127.0.0.1:5000/tags
```

## Architecture Notes

1. **Application Factory**: `create_app()` defers app creation for testability and clean configuration.
2. **Layered structure**: `models` (persistence) → `schemas` (contracts) → `resources` (HTTP).
3. **Flask-Smorest Blueprints**: one Blueprint per domain with auto-generated OpenAPI docs.
4. **Marshmallow validation**: input validated at the HTTP boundary.
5. **JWT for writes only**: read endpoints are public; mutations use `@jwt_required()`.
6. **Association table `items_tags`**: standard SQLAlchemy many-to-many.
7. **Password hashing**: Werkzeug `generate_password_hash`; never store plaintext.
8. **Unified error JSON**: HTTP and JWT errors return `{"message": "..."}`.

## License

For educational use; free to modify and present.
