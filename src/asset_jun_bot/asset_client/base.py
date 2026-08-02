# -*- coding: utf-8 -*-
"""AssetManager API 클라이언트 공통 헬퍼 모듈입니다 (AssetApiClient 위임)."""

import httpx
from ..config import Config
from .models import AssetClientError
from .client import get_default_client


def load_config() -> Config:
  """설정 객체를 로드하고 실패 시 AssetClientError를 발생시킵니다."""
  try:
    return Config.load()
  except ValueError as err:
    raise AssetClientError(f"설정 로드 중 오류 발생: {err}") from err


def handle_api_exception(exc: Exception) -> None:
  """httpx 예외 및 기타 일반 예외를 AssetClientError로 변환하여 발생시킵니다."""
  get_default_client().handle_exception(exc)
