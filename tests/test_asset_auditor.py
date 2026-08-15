# -*- coding: utf-8 -*-
"""asset-auditor 스킬 로딩 및 동작 검증 테스트 모듈입니다."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import os
from asset_jun_bot.agent_runner import AgentRunner


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
  """테스트 환경 변수를 주입합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345")
  monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")
  monkeypatch.setenv("STORAGE_DIR", "mock_storage_dir")
  monkeypatch.setenv("MODEL_CHAT", "gemini-3.5-flash")
  monkeypatch.setenv("NAVER_API_CLIENT_ID", "mock_naver_id")
  monkeypatch.setenv("NAVER_API_CLIENT_SECRET", "mock_naver_secret")


@pytest.mark.asyncio
async def test_agent_runner_includes_asset_auditor_skill(mocker):
  """AgentRunner가 설정한 skills_paths에 asset-auditor 스킬 경로가 포함되어 있는지 테스트합니다."""
  mock_config = MagicMock()
  mock_config.model_chat = "gemini-3.5-flash"

  # Agent 모킹
  mock_agent = MagicMock()
  mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
  mock_agent.__aexit__ = AsyncMock(return_value=None)
  mock_response = MagicMock()
  mock_response.text = AsyncMock(return_value="자산점검 시작합니다.")
  mock_agent.chat = AsyncMock(return_value=mock_response)

  mocker.patch("asset_jun_bot.agent_runner.Agent", return_value=mock_agent)
  mock_local_config = mocker.patch("asset_jun_bot.agent_runner.LocalAgentConfig")

  runner = AgentRunner(config=mock_config)
  response = await runner.ask("자산점검 시작해줘")

  assert response == "자산점검 시작합니다."
  mock_local_config.assert_called_once()
  kwargs = mock_local_config.call_args.kwargs
  
  # skills_paths가 전달되었고 그 하위에 asset-auditor 스킬 디렉터리가 존재하는지 확인
  skills_paths = kwargs.get("skills_paths", [])
  assert len(skills_paths) > 0
  
  # 실제 로컬 디렉터리에 asset-auditor/SKILL.md가 있는지 검증
  found_asset_auditor = False
  for path in skills_paths:
    target_skill_path = os.path.join(path, "asset-auditor", "SKILL.md")
    if os.path.exists(target_skill_path):
      found_asset_auditor = True
      break
  
  assert found_asset_auditor is True


def test_asset_auditor_references_structure():
  """asset-auditor 내부에 필수 references 파일들이 위치하고 유효한 내용을 포함하는지 검증합니다."""
  current_dir = os.path.dirname(os.path.abspath(__file__))
  skill_dir = os.path.abspath(os.path.join(current_dir, "..", ".agents", "skills", "asset-auditor"))

  skill_md = os.path.join(skill_dir, "SKILL.md")
  principles_md = os.path.join(skill_dir, "references", "investment-principles.md")
  index_md = os.path.join(skill_dir, "references", "trade-cases-index.md")
  case_md = os.path.join(skill_dir, "references", "cases", "001_samsung_hynix_semiconductor_2026.md")

  assert os.path.exists(skill_md)
  assert os.path.exists(principles_md)
  assert os.path.exists(index_md)
  assert os.path.exists(case_md)

  # 내용 무결성 검증
  with open(skill_md, "r", encoding="utf-8") as f:
    skill_content = f.read()
    assert "name: asset-auditor" in skill_content
    assert "references/investment-principles.md" in skill_content
    assert "references/trade-cases-index.md" in skill_content

  with open(principles_md, "r", encoding="utf-8") as f:
    principles_content = f.read()
    assert "손절 및 포지션 관리" in principles_content

  with open(index_md, "r", encoding="utf-8") as f:
    index_content = f.read()
    assert "001_samsung_hynix_semiconductor_2026.md" in index_content


def test_asset_advisor_skill_removed():
  """asset-advisor 스킬 디렉터리가 완전히 제거되었는지 검증합니다."""
  current_dir = os.path.dirname(os.path.abspath(__file__))
  advisor_dir = os.path.abspath(os.path.join(current_dir, "..", ".agents", "skills", "asset-advisor"))

  assert not os.path.exists(advisor_dir)


