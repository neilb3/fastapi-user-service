import os

os.environ["API_TOKENS"] = "dev-token-123:developer,admin-token-456:admin"
os.environ["TOKEN_EXPIRY_SECONDS"] = "86400"
os.environ["RATE_LIMIT_PER_MINUTE"] = "3"