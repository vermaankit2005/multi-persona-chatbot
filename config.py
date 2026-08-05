import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class Settings(BaseModel):
    GROQ_API_KEY: str
    POSTGRES_URL: str
    CLERK_SECRET_KEY: str
    # Sites allowed to present a token to this API. A token minted for someone
    # else's Clerk app fails the check instead of being accepted.
    CLERK_AUTHORIZED_PARTIES: list[str]

settings = Settings(
    GROQ_API_KEY=os.getenv("GROQ_API_KEY"),
    POSTGRES_URL=os.getenv("POSTGRES_URL"),
    CLERK_SECRET_KEY=os.getenv("CLERK_SECRET_KEY"),
    CLERK_AUTHORIZED_PARTIES=os.getenv(
        "CLERK_AUTHORIZED_PARTIES", "http://localhost:8000"
    ).split(","),
)
