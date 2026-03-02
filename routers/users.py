"""
Users router for DoorDash-like food delivery app.

Endpoints:
  GET   /api/users              — list users
  POST  /api/users              — create / resolve a user
  GET   /api/users/{user_id}    — get a single user
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/users", tags=["users"])

# In-memory user store — seeded with the demo user the SPA uses
_users_db: dict = {
    "user1": {"user_id": "user1", "name": "Demo User", "email": "demo@example.com"},
}


class UserCreateRequest(BaseModel):
    user_id: str = "user1"
    name: str = "Demo User"
    email: str = "demo@example.com"


# ---------------------------------------------------------------------------
# GET /api/users
# ---------------------------------------------------------------------------

@router.get("", summary="List users")
def list_users() -> dict:
    """Return all registered users."""
    return {"users": list(_users_db.values())}


# ---------------------------------------------------------------------------
# POST /api/users
# ---------------------------------------------------------------------------

@router.post("", summary="Create or resolve a user", status_code=201)
def create_user(body: UserCreateRequest) -> dict:
    """
    Create a user or return the existing one if the user_id already exists.
    The demo SPA sends user_id='user1'; this ensures the backend always
    has a matching record.
    """
    user_id = body.user_id
    if user_id in _users_db:
        # Idempotent: return the existing record rather than erroring
        return _users_db[user_id]

    user = {"user_id": user_id, "name": body.name, "email": body.email}
    _users_db[user_id] = user
    return user


# ---------------------------------------------------------------------------
# GET /api/users/{user_id}
# ---------------------------------------------------------------------------

@router.get("/{user_id}", summary="Get a user by ID")
def get_user(user_id: str) -> dict:
    """Return user info. Raises 404 via HTTPException if the user is not found."""
    user = _users_db.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")
    return user
