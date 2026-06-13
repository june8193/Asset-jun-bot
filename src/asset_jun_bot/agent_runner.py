# -*- coding: utf-8 -*-
"""Antigravity SDK를 사용하여 AI 에이전트와 대화하는 모듈입니다."""

import logging
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import policy
from .asset_client import get_asset_summary

logger = logging.getLogger(__name__)


class AgentRunner:
  """Antigravity SDK 에이전트 인터페이스를 래핑하는 클래스입니다."""

  def __init__(self):
    """AgentRunner를 초기화합니다."""
    # 시스템 명령 지침 정의
    self.system_instructions = (
        "당신은 준과 성은 부부의 통합 자산 관리 도우미 AI 챗봇(Asset-jun-bot)입니다.\n"
        "자산 정보 조회 요청이 있으면 등록된 get_asset_summary 도구(Tool)를 사용하여 최신 데이터를 실시간으로 조회하여 답변하십시오.\n"
        "사용자 자산에 대해 자연스럽고 친절한 한국어로 분석 및 요약을 제공하며, 수치는 원화(원) 단위로 콤마를 사용하여 가독성 있게 표현하십시오."
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
        tools=[get_asset_summary],
        policies=[
            policy.deny_all(),
            policy.allow(get_asset_summary.__name__),
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
