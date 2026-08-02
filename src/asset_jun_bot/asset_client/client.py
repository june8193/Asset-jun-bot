# -*- coding: utf-8 -*-
"""AssetManager API 통신을 전담하는 Deep Gateway Client 모듈입니다."""

import logging
from typing import TypeVar, Type, Any, Optional
import httpx
from pydantic import BaseModel
from ..config import Config
from .models import AssetClientError

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class AssetApiClient:
  """AssetManager 백엔드 API와의 세션, 타임아웃, 예외 변환 및 자동 응답 파싱을 관장하는 클라이언트입니다."""

  def __init__(self, base_url: str | None = None, timeout: float = 30.0):
    """AssetApiClient 인스턴스를 생성합니다."""
    self._base_url = base_url
    self.timeout = timeout

  def get_base_url(self) -> str:
    """설정 객체로부터 베이스 URL을 결정하여 반환합니다."""
    if self._base_url:
      return self._base_url.rstrip("/")
    try:
      config = Config.load()
      return config.asset_manager_api_url.rstrip("/")
    except Exception as err:
      raise AssetClientError(f"설정 로드 중 오류 발생: {err}") from err

  def handle_exception(self, exc: Exception) -> None:
    """httpx 및 기타 통신 예외를 AssetClientError로 전환하여 발생시킵니다."""
    if isinstance(exc, AssetClientError):
      raise exc
    elif isinstance(exc, httpx.HTTPStatusError):
      raise AssetClientError(
          f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
      ) from exc
    elif isinstance(exc, httpx.RequestError):
      raise AssetClientError(
          f"AssetManager API 서버 연결 네트워크 오류: {exc}"
      ) from exc
    else:
      raise AssetClientError(f"알 수 없는 오류 발생: {exc}") from exc

  async def get_json(
      self,
      endpoint: str,
      params: dict | None = None,
      response_model: Optional[Type[T]] = None,
  ) -> Any:
    """HTTP GET 요청을 수행하고 결과를 JSON 또는 Pydantic 모델로 변환하여 반환합니다."""
    base_url = self.get_base_url()
    url = f"{base_url}{endpoint}"

    try:
      async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if response_model is not None:
          return response_model.model_validate(data)
        return data
    except Exception as exc:
      self.handle_exception(exc)

  async def post_json(
      self,
      endpoint: str,
      params: dict | None = None,
      json_data: dict | None = None,
      response_model: Optional[Type[T]] = None,
  ) -> Any:
    """HTTP POST 요청을 수행하고 결과를 JSON 또는 Pydantic 모델로 변환하여 반환합니다."""
    base_url = self.get_base_url()
    url = f"{base_url}{endpoint}"

    try:
      async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.post(url, params=params, json=json_data)
        response.raise_for_status()
        data = response.json()

        if response_model is not None:
          return response_model.model_validate(data)
        return data
    except Exception as exc:
      self.handle_exception(exc)


# 글로벌 모듈 래퍼용 기본 클라이언트 인스턴스
_default_client = AssetApiClient()


def get_default_client() -> AssetApiClient:
  """기본 싱글톤 AssetApiClient 인스턴스를 반환합니다."""
  return _default_client
