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

      total_asset = data.get("total_valuation_krw", 0)
      total_debt = 0  # 백엔드 API에서 부채 정보를 제공하지 않으므로 0으로 설정
      net_worth = total_asset - total_debt
      roi = data.get("cumulative_roi", 0.0)

      # 보기 좋은 마크다운 텍스트 포맷팅
      summary = (
          "📊 **자산 요약 정보**\n"
          f"- 총 자산: {int(total_asset):,}원\n"
          f"- 총 부채: {int(total_debt):,}원\n"
          f"- 순자산: {int(net_worth):,}원\n"
          f"- 투자수익률 (ROI): {roi:.2f}%"
      )
      return summary

  except httpx.HTTPStatusError as exc:
    return f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
  except httpx.RequestError as exc:
    return f"AssetManager API 서버 연결 네트워크 오류: {exc}"
  except Exception as exc:
    return f"알 수 없는 오류 발생: {exc}"


async def get_asset_ratios() -> str:
  """AssetManager API로부터 자산군별 백분율 비중 정보를 조회합니다.

  이 함수는 에이전트의 도구(Tool)로 등록되므로 상세한 docstring이 작성되어야 합니다.

  Returns:
      자산군별 백분율 비중 현황을 포함하는 한국어 요약 텍스트 또는 오류 메시지
  """
  try:
    config = Config.load()
  except ValueError as err:
    return f"설정 로드 중 오류 발생: {err}"

  url = f"{config.asset_manager_api_url}/api/ratios/rebalancing"

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url)
      response.raise_for_status()
      data = response.json()

      major_results = data.get("major_results", [])
      if not major_results:
        return "📊 **자산군별 비중 현황**\n등록된 자산 데이터가 없습니다."

      lines = ["📊 **자산군별 비중 현황**"]
      for item in major_results:
        category = item.get("category", "미분류")
        current_amt = item.get("current_amt", 0.0)
        current_ratio = item.get("current_ratio", 0.0)
        lines.append(f"- {category}: {current_ratio:.2f}% ({current_amt:,.0f}원)")

      return "\n".join(lines)

  except httpx.HTTPStatusError as exc:
    return f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
  except httpx.RequestError as exc:
    return f"AssetManager API 서버 연결 네트워크 오류: {exc}"
  except Exception as exc:
    return f"알 수 없는 오류 발생: {exc}"


async def get_watchlist_prices(country: str = "KR") -> str:
  """AssetManager API로부터 특정 국가의 관심종목 실시간 시세를 조회합니다.

  이 함수는 에이전트의 도구(Tool)로 등록되므로 상세한 docstring이 작성되어야 합니다.

  Args:
      country: 조회할 국가 구분 ("KR" 또는 "US", 기본값 "KR")

  Returns:
      관심종목명, 현재가, 등락률 정보를 포맷팅한 한국어 텍스트 또는 오류 메시지
  """
  try:
    config = Config.load()
  except ValueError as err:
    return f"설정 로드 중 오류 발생: {err}"

  url = f"{config.asset_manager_api_url}/api/watchlist/prices"
  params = {"country": country.upper()}

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url, params=params)
      response.raise_for_status()
      data = response.json()

      if not data:
        return f"📈 **관심종목 시세 정보 ({country.upper()})**\n등록된 관심종목이 없습니다."

      lines = [f"📈 **관심종목 시세 정보 ({country.upper()})**"]
      unit = "$" if country.upper() == "US" else "원"

      for item in data:
        stock_name = item.get("stock_name", "")
        stock_code = item.get("stock_code", "")
        current_price = item.get("current_price", 0.0)
        change_rate = item.get("change_rate", 0.0)

        # 등락률 포맷팅 (+ 기호 명시)
        rate_str = f"{change_rate:+.2f}%"
        lines.append(
            f"- {stock_name} ({stock_code}): {current_price:,.0f}{unit} ({rate_str})"
            if country.upper() != "US"
            else f"- {stock_name} ({stock_code}): {unit}{current_price:,.2f} ({rate_str})"
        )

      return "\n".join(lines)

  except httpx.HTTPStatusError as exc:
    return f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
  except httpx.RequestError as exc:
    return f"AssetManager API 서버 연결 네트워크 오류: {exc}"
  except Exception as exc:
    return f"알 수 없는 오류 발생: {exc}"

