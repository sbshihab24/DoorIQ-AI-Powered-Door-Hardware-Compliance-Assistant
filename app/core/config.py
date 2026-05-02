from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DoorIQ Chatbot API"
    app_env: str = "development"
    app_debug: bool = False
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/dooriq"
    openai_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    local_embedding_dimensions: int = 128

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
