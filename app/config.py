from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    admin_ids: str = ""

    database_url: str = (
        "postgresql+asyncpg://lotex:change_me@localhost:5432/lotex"
    )

    bot_public_name: str = "LOTEX SHOP"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def admins(self) -> set[int]:
        return {
            int(x.strip())
            for x in self.admin_ids.split(",")
            if x.strip().isdigit()
        }


settings = Settings()
