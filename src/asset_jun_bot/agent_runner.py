# -*- coding: utf-8 -*-
"""Antigravity SDK를 사용하여 AI 에이전트와 대화하는 모듈입니다."""

import logging
from typing import Literal
from pydantic import BaseModel, Field
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import policy
from .asset_client import (
    get_asset_summary,
    get_asset_ratios,
    get_watchlist_prices,
    AssetClientError,
)

logger = logging.getLogger(__name__)


class TaskRouting(BaseModel):
  """사용자 메시지의 의도를 분류하여 적합한 작업 유형으로 매핑합니다."""

  task_type: Literal["GENERAL_CONVERSATION", "ASSET_INQUIRY"] = Field(
      description=(
          "사용자의 질문에 알맞은 작업 유형입니다. "
          "'GENERAL_CONVERSATION'은 일상 대화, 인사, 챗봇 소개, 사용법 안내 등이고, "
          "'ASSET_INQUIRY'는 총자산 현황, 자산 비중, 누적 수익률, 종목 현재가, "
          "자산 보고서 등 실제 자산 데이터를 조회(Tool calling)해야만 하는 질문입니다."
      )
  )


class AgentRunner:
  """Antigravity SDK 에이전트 인터페이스를 래핑하는 클래스입니다."""

  def __init__(self, config=None):
    """AgentRunner를 초기화합니다.

    Args:
        config: 로드 완료된 설정 객체. 지정되지 않은 경우 Config.load()로 가져옵니다.
    """
    if config is None:
      from .config import Config
      try:
        self.config = Config.load()
      except Exception:
        # 테스트 환경이나 설정 누락 시 하위 호환 및 테스트 격리를 위해 더미 설정 할당
        self.config = None
    else:
      self.config = config

    # 시스템 명령 지침 정의
    self.system_instructions_asset = (
        "당신은 준과 성은 부부의 통합 자산 관리 도우미 AI 챗봇(Asset-jun-bot)입니다.\n"
        "다음과 같이 적절한 도구(Tool)를 실시간으로 조회하여 친절하게 한국어로 답변하십시오:\n"
        "1. 총자산, 총 투자 원금, 누적 투자 수익, 투자수익률 등 요약 요청: get_asset_summary 도구 사용\n"
        "2. 자산군별 백분율 비중(현금, 주식 등) 요청: get_asset_ratios 도구 사용\n"
        "3. 관심종목 시세 및 실시간 주가 요청 (예: '국내 관심종목 가격 어때?', '미국 종목 보여줘'): get_watchlist_prices 도구 사용 (국가 구분에 따라 country='KR' 또는 country='US' 인자 전달)\n"
        "각 도구(Tool)는 가공되지 않은 자산 데이터를 객체 형태로 반환합니다. 이 데이터를 바탕으로 사용자에게 친절하게 한국어 자연어와 가독성 있는 마크다운 서식을 활용해 브리핑해 주십시오.\n"
        "⚠️ 중요: 텔레그램 메신저는 마크다운 표(Table, |---| 구문)를 지원하지 않아 깨져서 보입니다. 따라서 정보를 출력할 때 절대로 표(Table) 구문을 사용하지 말고, 대신 이모지(Emoji), 줄 바꿈, 그리고 강조(굵은 글씨)가 들어간 리스트(bullet points) 서식을 사용하여 모바일 화면에서도 깨짐 없이 한눈에 들어오도록 구성하십시오.\n"
        "비정상적인 투자 리밸런싱 조언이나 과도한 미래 주가 예측은 피하십시오."
    )

    self.system_instructions_chat = (
        "당신은 준과 성은 부부의 통합 자산 관리 도우미 AI 챗봇(Asset-jun-bot)입니다.\n"
        "현재 질문은 일반 대화 또는 인사로 판단되었습니다.\n"
        "친절하고 따뜻하게 인사를 건네거나 사용자 질문에 한국어로 답해주세요.\n"
        "자산 정보 조회나 주가/비중 계산이 필요한 경우 해당 기능을 요청해 달라고 자연스럽게 안내하셔도 좋습니다.\n"
        "표(Table) 서식은 절대로 사용하지 마십시오."
    )

    self.router_instructions = (
        "사용자의 질문을 분석하여 가장 알맞은 task_type을 분류해 주세요.\n"
        " - GENERAL_CONVERSATION: 인사, 잡담, 봇의 자기소개, 명령어 사용법 질문 등 자산 데이터를 호출할 필요가 없는 단순 대화.\n"
        " - ASSET_INQUIRY: 자산 비중, 총 자산 요약, 관심종목 가격 조회, 수익률 통계 등 자산 API 도구를 호출해야만 정확히 대답할 수 있는 모든 질문.\n"
    )

  async def _route_intent(self, prompt: str) -> str:
    """사용자의 입력을 분석하여 작업 유형을 반환합니다.

    Args:
        prompt: 사용자 질문

    Returns:
        분류된 작업 유형 ("GENERAL_CONVERSATION" 또는 "ASSET_INQUIRY")
    """
    if not self.config or not getattr(self.config, "model_router", None):
      return "GENERAL_CONVERSATION"

    router_config = LocalAgentConfig(
        model=self.config.model_router,
        system_instructions=self.router_instructions,
        response_schema=TaskRouting,
        tools=[],
        policies=[policy.deny_all()],
    )

    try:
      async with Agent(router_config) as agent:
        response = await agent.chat(prompt)
        text = await response.text()
        
        # Pydantic을 활용해 JSON 파싱 수행
        routing_result = TaskRouting.model_validate_json(text)
        logger.info(f"의도 분류 결과: {routing_result.task_type} (입력: {prompt})")
        return routing_result.task_type
    except Exception as exc:
      logger.warning(f"의도 분류(Routing) 중 예외 발생, GENERAL_CONVERSATION으로 폴백합니다. 에러: {exc}")
      return "GENERAL_CONVERSATION"

  async def ask(self, prompt: str) -> str:
    """사용자의 프롬프트를 분석하여 작업 유형에 맞게 모델과 도구를 동적으로 선택해 실행합니다.

    Args:
        prompt: 사용자 질문

    Returns:
        에이전트의 답변 텍스트 (에러 발생 시 에러 요약 메시지)
    """
    # 1. 의도 분류 실행
    task_type = await self._route_intent(prompt)

    # 2. 작업에 따른 설정 동적 구성
    if task_type == "ASSET_INQUIRY":
      model_name = self.config.model_asset_inquiry if self.config else "gemini-1.5-flash"
      system_instructions = self.system_instructions_asset
      tools = [get_asset_summary, get_asset_ratios, get_watchlist_prices]
      policies = [
          policy.deny_all(),
          policy.allow(get_asset_summary.__name__),
          policy.allow(get_asset_ratios.__name__),
          policy.allow(get_watchlist_prices.__name__),
      ]
    else:  # GENERAL_CONVERSATION 및 기타 폴백
      model_name = self.config.model_general_conversation if self.config else "gemini-2.5-flash"
      system_instructions = self.system_instructions_chat
      tools = []
      policies = [policy.deny_all()]

    config = LocalAgentConfig(
        model=model_name,
        system_instructions=system_instructions,
        tools=tools,
        policies=policies,
    )

    try:
      async with Agent(config) as agent:
        response = await agent.chat(prompt)
        text = await response.text()
        return text
    except AssetClientError as exc:
      logger.warning(f"자산 API 클라이언트 에러 발생: {exc}")
      return "⚠️ API 서버에 연결할 수 없습니다."
    except Exception as exc:
      logger.exception("Gemini 에이전트 실행 중 예외 발생")
      return f"⚠️ Gemini 에이전트 실행 중 에러가 발생했습니다: {exc}"
