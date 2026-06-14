# -*- coding: utf-8 -*-
"""Antigravity SDK를 사용하여 AI 에이전트와 대화하는 모듈입니다."""

import logging
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import policy
from .asset_client import get_asset_summary, get_asset_ratios, get_watchlist_prices

logger = logging.getLogger(__name__)


class AgentRunner:
  """Antigravity SDK 에이전트 인터페이스를 래핑하는 클래스입니다."""

  def __init__(self):
    """AgentRunner를 초기화합니다."""
    # 시스템 명령 지침 정의
    self.system_instructions = (
        "당신은 준과 성은 부부의 통합 자산 관리 도우미 AI 챗봇(Asset-jun-bot)입니다.\n"
        "다음과 같이 적절한 도구(Tool)를 실시간으로 조회하여 친절하게 한국어로 답변하십시오:\n"
        "1. 총자산, 순자산 등 기본 재무 현황 요약 요청: get_asset_summary 도구 사용\n"
        "2. 자산군별 백분율 비중(현금, 주식 등) 요청: get_asset_ratios 도구 사용\n"
        "3. 관심종목 시세 및 실시간 주가 요청 (예: '국내 관심종목 가격 어때?', '미국 종목 보여줘'): get_watchlist_prices 도구 사용 (국가 구분에 따라 country='KR' 또는 country='US' 인자 전달)\n"
        "비정상적인 투자 리밸런싱 조언이나 과도한 미래 주가 예측은 피하고, 현재 수치 데이터를 가독성 있게 브리핑해 주십시오."
    )

  async def ask(self, prompt: str) -> str:
    """사용자의 프롬프트를 에이전트에 보내고 응답을 받아옵니다.

    Args:
        prompt: 사용자 질문

    Returns:
        에이전트의 답변 텍스트 (에러 발생 시 에러 요약 메시지)
    """
    config = LocalAgentConfig(
        system_instructions=self.system_instructions,
        tools=[get_asset_summary, get_asset_ratios, get_watchlist_prices],
        policies=[
            policy.deny_all(),
            policy.allow(get_asset_summary.__name__),
            policy.allow(get_asset_ratios.__name__),
            policy.allow(get_watchlist_prices.__name__),
        ],
    )

    try:
      async with Agent(config) as agent:
        response = await agent.chat(prompt)
        text = await response.text()
        return text
    except Exception as exc:
      logger.exception("Gemini 에이전트 실행 중 예외 발생")
      return f"⚠️ Gemini 에이전트 실행 중 에러가 발생했습니다: {exc}"
