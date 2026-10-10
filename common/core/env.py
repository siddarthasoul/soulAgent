import os

from dotenv import load_dotenv


load_dotenv()


class Env:
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL",
    )

    OLLAMA_MODEL: str = os.getenv(
        "OLLAMA_MODEL",
    )

    QDRANT_HOST: str = os.getenv("QDRANT_HOST")

    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT"))

    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")

    GEMINI_IMAGE_MODEL: str = os.getenv(
        "GEMINI_IMAGE_MODEL",
    )

    GEMINI_MODEL: str = os.getenv(
        "GEMINI_MODEL",
    )

    NVIDIA_API_KEY: str | None = os.getenv("NVIDIA_API_KEY")

    NVIDIA_BASE_URL: str | None = os.getenv("NVIDIA_BASE_URL")

    NVIDIA_MODEL: str | None = os.getenv("NVIDIA_MODEL")

    BRAVE_SEARCH_API_KEY: str | None = os.getenv("BRAVE_SEARCH_API_KEY")


env = Env()