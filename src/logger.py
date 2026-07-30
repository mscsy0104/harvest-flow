import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from config import LOG_DIR

LOGGER_NAME = "harvest_flow"
LOG_FILE = LOG_DIR / "harvest.log"

def setup_logger(name: str = LOGGER_NAME) -> logging.Logger:
    """하루 단위로 회전하는 HarvestFlow 로거를 설정합니다."""
    logger = logging.getLogger(name)

    # 부모(root) 핸들러가 있어도, 이 로거 자체에 핸들러가 있으면 재등록하지 않음
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] (%(filename)s:%(lineno)d) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        filename=LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=14,
        encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def read_recent_logs(n: int = 30) -> str:
    """대시보드용으로 최근 n줄을 읽습니다. 파일이 없으면 빈 문자열."""
    if not LOG_FILE.exists():
        return ""
    with LOG_FILE.open(encoding="utf-8") as f:
        return "".join(f.readlines()[-n:])


logger = setup_logger()
