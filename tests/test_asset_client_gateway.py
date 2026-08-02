# -*- coding: utf-8 -*-
"""AssetApiClient Gateway 단위 테스트입니다."""

import pytest
import respx
import httpx
from asset_jun_bot.asset_client.client import AssetApiClient
from asset_jun_bot.asset_client.models import AssetClientError, AssetSummaryResponse


@pytest.mark.asyncio
async def test_asset_api_client_get_json_success():
  """AssetApiClient가 HTTP GET 응답을 정상적으로 수신하고 Pydantic 모델로 파싱함을 검증합니다."""
  mock_url = "http://localhost:8000/api/v1/assets/summary"
  mock_data = {
      "total_valuation_krw": 10000000.0,
      "total_principal": 8000000.0,
      "total_profit": 2000000.0,
      "cumulative_roi": 25.0,
      "contribution_ratio": 80.0,
      "profit_ratio": 20.0,
      "exchange_rate": {"date": "2026-08-01", "rate": 1350.0},
      "latest_price_date": "2026-08-01",
  }

  async with respx.mock:
    respx.get(mock_url).respond(status_code=200, json=mock_data)

    client = AssetApiClient(base_url="http://localhost:8000")
    result = await client.get_json("/api/v1/assets/summary", response_model=AssetSummaryResponse)

    assert isinstance(result, AssetSummaryResponse)
    assert result.total_valuation_krw == 10000000.0
    assert result.cumulative_roi == 25.0


@pytest.mark.asyncio
async def test_asset_api_client_post_json_success():
  """AssetApiClient가 HTTP POST 요청을 성공적으로 수행함을 검증합니다."""
  mock_url = "http://localhost:8000/api/kiwoom/sync-transactions"
  mock_resp = {"status": "success", "synced": 5}

  async with respx.mock:
    respx.post(mock_url).respond(status_code=200, json=mock_resp)

    client = AssetApiClient(base_url="http://localhost:8000")
    result = await client.post_json("/api/kiwoom/sync-transactions", params={"days": 7})

    assert result == mock_resp


@pytest.mark.asyncio
async def test_asset_api_client_http_error_handling():
  """AssetApiClient가 HTTP 에러 시 AssetClientError로 일관되게 변환함을 검증합니다."""
  mock_url = "http://localhost:8000/api/v1/assets/summary"

  async with respx.mock:
    respx.get(mock_url).respond(status_code=500)

    client = AssetApiClient(base_url="http://localhost:8000")
    with pytest.raises(AssetClientError) as exc_info:
      await client.get_json("/api/v1/assets/summary")

    assert "HTTP 오류 코드: 500" in str(exc_info.value)


@pytest.mark.asyncio
async def test_asset_api_client_network_request_error():
  """AssetApiClient가 네트워크 접속 장애 시 RequestError를 AssetClientError로 변환함을 검증합니다."""
  mock_url = "http://localhost:8000/api/v1/assets/summary"

  async with respx.mock:
    respx.get(mock_url).side_effect = httpx.RequestError("Connection refused")

    client = AssetApiClient(base_url="http://localhost:8000")
    with pytest.raises(AssetClientError) as exc_info:
      await client.get_json("/api/v1/assets/summary")

    assert "네트워크 오류" in str(exc_info.value)
