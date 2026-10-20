import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.logging import RichHandler

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Base paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    SOLUTIONS_DIR: Path = BASE_DIR / "data" / "solutions"
    REPORTS_DIR: Path = BASE_DIR / "data" / "reports"
    PROBLEMS_DIR: Path = BASE_DIR / "data" / "problems"
    LOGS_DIR: Path = BASE_DIR / "logs"
    BROWSER_PROFILE_DIR: Path = BASE_DIR / "data" / "browser_profile"
    NEETCODE_MANIFEST_PATH: Path = BASE_DIR / "data" / "neetcode150.json"

    # Ollama LLM Configuration
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_TEMPERATURE: float = 0.2
    OLLAMA_TIMEOUT_SECONDS: int = 120

    # Account Verification (Critical)
    EXPECTED_LEETCODE_USERNAME: str = ""

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'leetcode_automator.db'}"

    # Submission & Safety Controls
    AUTO_SUBMIT: bool = False
    MAX_REPAIR_ATTEMPTS: int = 3
    MAX_SUBMISSIONS_PER_PROBLEM: int = 3
    SUBMISSION_TIMEOUT_SECONDS: int = 120

    # Browser
    BROWSER_HEADLESS: bool = False

    # Subprocess execution limits
    TEST_EXECUTION_TIMEOUT_SECONDS: int = 5
    MAX_OUTPUT_CHARS: int = 50_000

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    LOG_FILE_BACKUP_COUNT: int = 5

    # LeetCode Endpoints
    LEETCODE_GRAPHQL_URL: str = "https://leetcode.com/graphql"
    LEETCODE_BASE_URL: str = "https://leetcode.com"

settings = Settings()

# Ensure directories exist
for folder in [
    settings.DATA_DIR,
    settings.SOLUTIONS_DIR,
    settings.REPORTS_DIR,
    settings.PROBLEMS_DIR,
    settings.LOGS_DIR,
    settings.BROWSER_PROFILE_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)

def setup_logging(level: str | None = None) -> logging.Logger:
    """Configures rotating file logging and console rich logging."""
    log_level = getattr(logging, (level or settings.LOG_LEVEL).upper(), logging.INFO)
    logger = logging.getLogger("leetcode_automator")
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers on multiple calls
    if not logger.handlers:
        # Rotating File Handler
        log_file = settings.LOGS_DIR / "leetcode_automator.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=settings.LOG_FILE_MAX_BYTES,
            backupCount=settings.LOG_FILE_BACKUP_COUNT,
            encoding="utf-8"
        )
        file_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] (%(name)s:%(module)s:%(lineno)d) - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

        # Rich Console Handler
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=False,
            markup=True
        )
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)

    return logger

logger = setup_logging()
