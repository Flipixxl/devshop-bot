import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(value: str | None) -> list[int]:
    if not value:
        return []
    return [int(part.strip()) for part in value.split(",") if part.strip()]


@dataclass(frozen=True)
class Config:
    bot_token: str
    webapp_url: str
    admin_ids: list[int] = field(default_factory=list)
    host: str = "0.0.0.0"
    port: int = 8080
    data_dir: str = "."


def load_config() -> Config:
    return Config(
        bot_token=os.getenv("BOT_TOKEN", "").strip(),
        webapp_url=os.getenv("WEBAPP_URL", "").strip(),
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        data_dir=os.getenv("DATA_DIR", ".").strip() or ".",
    )
