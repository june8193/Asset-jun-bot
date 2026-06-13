# -*- coding: utf-8 -*-
"""AssetManager API와 통신하여 자산 정보를 가져오는 클라이언트 모듈입니다."""

import httpx
from .config import Config


async def get_asset_summary() -> str:
  """AssetManager API로부터 자산 요약 정보를 조회합니다.

  이 함수는 에이전트의 도구(Tool)로 등록되므로 상세한 docstring이 작성되어야 합니다.

  Returns:
      자산 총액, 부채, 순자산, 수익률을 포함하는 한국어 요약 텍스트 또는 오류 메시지
  """
  try:
    config = Config.load()
  except ValueError as err:
    return f"설정 로드 중 오류 발생: {err}"

  url = f"{config.asset_manager_api_url}/api/dashboard/summary"

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url)
      response.raise_for_status()
      data = response.json()

      total_asset = data.get("total_asset", 0)
      total_debt = data.get("total_debt", 0)
      net_worth = data.get("net_worth", 0)
      roi = data.get("roi", 0.0)

      # 보기 좋은 마크다운 텍스트 포맷팅
      summary = (
          "📊 **자산 요약 정보**\n"
          f"- 총 자산: {total_asset:,}원\n"
          f"- 총 부채: {total_debt:,}원\n"
          f"- 순자산: {net_worth:,}원\n"
          f"- 투자수익률 (ROI): {roi:.2f}%"
      )
      return summary

  except httpx.HTTPStatusError as exc:
    return f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
  except httpx.RequestError as exc:
    return f"AssetManager API 서버 연결 네트워크 오류: {exc}"
  except Exception as exc:
    return f"알 수 없는 오류 발생: {exc}"
