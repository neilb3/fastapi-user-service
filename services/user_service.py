from models.user import UserCreate, UserResponse

MAX_NAME_LENGTH = 255
MAX_EMAIL_LENGTH = 255


class ValidationError(ValueError):
    pass


class UserService:
    def __init__(self):
        self._users: list[dict] = [
            {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "admin"},
            {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "user"},
            {"id": 3, "name": "Carol White", "email": "carol@example.com", "role": "user"},
        ]
        self._next_id = 4

    def _validate_user_input(self, name: str | None, email: str | None) -> None:
        if name is None:
            raise ValidationError("Name must not be None.")
        if not isinstance(name, str) or name.strip() == "":
            raise ValidationError("Name must not be empty.")
        if len(name) > MAX_NAME_LENGTH:
            raise ValidationError(
                f"Name must not exceed {MAX_NAME_LENGTH} characters."
            )

        if email is None:
            raise ValidationError("Email must not be None.")
        if not isinstance(email, str) or email.strip() == "":
            raise ValidationError("Email must not be empty.")
        if len(email) > MAX_EMAIL_LENGTH:
            raise ValidationError(
                f"Email must not exceed {MAX_EMAIL_LENGTH} characters."
            )

    def get_all_users(self) -> list[UserResponse]:
        return [UserResponse(**u) for u in self._users]

    def get_user_by_id(self, user_id: int) -> UserResponse | None:
        if user_id is None:
            raise ValidationError("User ID must not be None.")
        for user in self._users:
            if user["id"] == user_id:
                return UserResponse(**user)
        return None

    def create_user(self, user: UserCreate) -> UserResponse:
        self._validate_user_input(user.name, user.email)
        new_user = {
            "id": self._next_id,
            "name": user.name,
            "email": user.email,
            "role": user.role or "user"
        }
        self._users.append(new_user)
        self._next_id += 1
        return UserResponse(**new_user)