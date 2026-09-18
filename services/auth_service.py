from typing import Optional, Tuple, List
from werkzeug.security import generate_password_hash, check_password_hash
from repositories.user_repository import UserRepository
from models.user import User

class AuthService:
    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()

    def hash_password(self, password: str) -> str:
        return generate_password_hash(password)

    def check_password(self, plain_password: str, password_hash: str) -> bool:
        return check_password_hash(password_hash, plain_password)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        if not username or not password:
            return None
        user = self.user_repo.get_by_username(username.strip())
        if not user:
            return None
        if self.check_password(password, user.password_hash):
            return user
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.user_repo.get_by_id(user_id)

    def register_user(self, username: str, password: str, role: str) -> Tuple[bool, str, Optional[User]]:
        username = username.strip() if username else ""
        if not username:
            return False, "Username is required.", None
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters long.", None
        if role not in ("ADMIN", "INVESTIGATOR"):
            return False, "Role must be either ADMIN or INVESTIGATOR.", None

        existing = self.user_repo.get_by_username(username)
        if existing:
            return False, f"Username '{username}' is already taken.", None

        hashed = self.hash_password(password)
        created_user = self.user_repo.create(username, hashed, role)
        return True, "User registered successfully.", created_user

    def list_users(self) -> List[User]:
        return self.user_repo.list_all()
