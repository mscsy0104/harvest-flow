"""환경 변수 로딩 및 공통 파싱 유틸."""

from __future__ import annotations

import os

from dotenv import load_dotenv

# dotenv 로딩은 멱등적이므로 공통 모듈에서 1회 호출해도 안전합니다.
load_dotenv()


def get_env(name: str, default: str | None = None) -> str:
    """문자열 환경 변수를 읽고, 값이 없으면 default를 사용합니다."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        if default is None:
            raise RuntimeError(f"필수 환경 변수가 비어 있습니다: {name}")
        return default
    return value


def get_required_env(name: str) -> str:
    """필수 환경 변수를 읽습니다. 없거나 공백이면 즉시 예외를 냅니다."""
    return get_env(name, default=None)


def get_bool_env(name: str, default: bool = False) -> bool:
    """불리언 환경 변수를 읽습니다. (1/true/yes/on, 0/false/no/off 허용)"""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"불리언 환경 변수 파싱 실패: {name}={value!r}")


def get_int_env(name: str, default: int) -> int:
    """정수 환경 변수를 읽고, 값이 없으면 default를 사용합니다."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"정수 환경 변수 파싱 실패: {name}={value!r}") from exc
