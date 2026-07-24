# -*- coding: utf-8 -*-
"""AssetManager API 클라이언트 공통 헬퍼 모듈입니다."""

import httpx
from ..config import Config
from .models import AssetClientError


def load_config() -> Config:
  """설정 객체를 로드하고 실패 시 AssetClientError를 발생시킵니다."""
  try:
    return Config.load()
  except ValueError as err:
    raise AssetClientError(f"설정 로드 중 오류 발생: {err}") from err


def handle_api_exception(exc: Exception) -> None:
  """httpx 예외 및 기타 일반 예외를 AssetClientError로 변환하여 발생시킵니다."""
  if isinstance(exc, httpx.HTTPStatusError):
    raise AssetClientError(
        f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
    ) from exc
  elif isinstance(exc, httpx.RequestError):
    raise AssetClientError(
        f"AssetManager API 서버 연결 네트워크 오류: {exc}"
    ) from exc
  elif isinstance(exc, AssetClientError):
    raise exc
  else:
    raise AssetClientError(f"알 수 없는 오류 발생: {exc}") from exc
