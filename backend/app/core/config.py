from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://retail:retail@localhost:5432/retail"
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "retail"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-luna"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
