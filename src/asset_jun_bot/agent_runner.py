# -*- coding: utf-8 -*-
"""Antigravity SDK를 사용하여 AI 에이전트와 대화하는 모듈입니다."""

import os
import logging
from typing import Literal, Callable, Coroutine, Any
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import policy
from .asset_client import AssetClientError

logger = logging.getLogger(__name__)


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

    # 프로젝트 루트 및 스킬 디렉터리 경로 계산
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    self.skills_paths = [os.path.join(project_root, ".agents", "skills")]

  async def ask(
      self,
      prompt: str,
      on_status_update: Callable[[str], Coroutine[Any, Any, None]] | None = None,
  ) -> str:
    """사용자의 프롬프트를 분석하여 단일 모델과 스킬, 비즈니스 도구를 연동해 실행합니다.

    Args:
        prompt: 사용자 질문
        on_status_update: 상태 변화 발생 시 호출할 비동기 콜백 함수

    Returns:
        에이전트의 답변 텍스트 (에러 발생 시 에러 요약 메시지)
    """
    # 1. 상태 업데이트 콜백이 전달된 경우 호출 (하위 호환성 지원)
    if on_status_update:
      await on_status_update("CHAT")

    # 2. 단일 모델 및 도구, 정책 설정
    model_name = self.config.model_chat if self.config else "gemini-3.5-flash"
    tools = []
    policies = [
        policy.deny_all(),
        policy.allow("run_command"),
    ]

    config = LocalAgentConfig(
        model=model_name,
        tools=tools,
        policies=policies,
        skills_paths=self.skills_paths,
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
