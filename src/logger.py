import logging
from logging.handlers import TimedRotatingFileHandler

from config import LOG_DIR, LOG_LEVEL

LOGGER_NAME = "harvest_flow"
LOG_FILE = LOG_DIR / "harvest.log"


def _resolve_log_level(level_name: str) -> int:
    level = getattr(logging, level_name, None)
    if isinstance(level, int):
        return level
    return logging.INFO

def setup_logger(name: str = LOGGER_NAME) -> logging.Logger:
    """하루 단위로 회전하는 HarvestFlow 로거를 설정합니다."""
    logger = logging.getLogger(name)

    # 부모(root) 핸들러가 있어도, 이 로거 자체에 핸들러가 있으면 재등록하지 않음
    if logger.handlers:
        return logger

    logger.setLevel(_resolve_log_level(LOG_LEVEL))
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
    if n <= 0 or not LOG_FILE.exists():
        return ""

    chunk_size = 4096
    newline_count = 0
    chunks: list[bytes] = []
    with LOG_FILE.open("rb") as f:
        f.seek(0, 2)
        file_size = f.tell()
        pos = file_size

        while pos > 0 and newline_count <= n:
            read_size = min(chunk_size, pos)
            pos -= read_size
            f.seek(pos)
            chunk = f.read(read_size)
            chunks.append(chunk)
            newline_count += chunk.count(b"\n")

    data = b"".join(reversed(chunks))
    lines = data.decode("utf-8", errors="replace").splitlines()
    return "\n".join(lines[-n:])


logger = setup_logger()
