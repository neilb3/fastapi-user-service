from models.user import UserCreate, UserResponse

MAX_TEXT_LENGTH = 5000


class SentimentScorer:
    def score(self, text: str) -> str:
        if text is None or not isinstance(text, str):
            raise TypeError("text must be a string, not None or another type")
        if not text.strip():
            raise ValueError("text must not be empty or whitespace-only")
        if len(text) > MAX_TEXT_LENGTH:
            raise ValueError(
                f"text must not exceed {MAX_TEXT_LENGTH} characters, got {len(text)}"
            )
        lower = text.lower()
        if any(word in lower for word in ("good", "great", "excellent", "happy", "love")):
            return "positive"
        if any(word in lower for word in ("bad", "terrible", "awful", "sad", "hate")):
            return "negative"
        return "neutral"


class UserService:
    def __init__(self):
        self._users: list[dict] = [
            {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "admin"},
            {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "user"},
            {"id": 3, "name": "Carol White", "email": "carol@example.com", "role": "user"},
        ]
        self._next_id = 4

    def get_all_users(self) -> list[UserResponse]:
        return [UserResponse(**u) for u in self._users]

    def get_user_by_id(self, user_id: int) -> UserResponse | None:
        for user in self._users:
            if user["id"] == user_id:
                return UserResponse(**user)
        return None

    def create_user(self, user: UserCreate) -> UserResponse:
        new_user = {
            "id": self._next_id,
            "name": user.name,
            "email": user.email,
            "role": user.role or "user"
        }
        self._users.append(new_user)
        self._next_id += 1
        return UserResponse(**new_user)