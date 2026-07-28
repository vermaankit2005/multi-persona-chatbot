import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class Settings(BaseModel):
    GROQ_API_KEY: str

settings = Settings(
    GROQ_API_KEY=os.getenv("GROQ_API_KEY")
)
