from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DoorIQ Chatbot API"
    app_env: str = "development"
    app_debug: bool = False
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/dooriq"
    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    groq_api_key: str | None = None
    groq_chat_model: str = "llama-3.3-70b-versatile"
    local_embedding_dimensions: int = 128

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
