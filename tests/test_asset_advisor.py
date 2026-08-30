# -*- coding: utf-8 -*-
"""asset-advisor 스킬 무결성 검증 테스트 모듈입니다."""

import os
import pytest


def test_asset_advisor_skill_integrity():
  """asset-advisor 스킬 파일이 올바르게 생성되고 필요한 규칙 및 레퍼런스를 참조하는지 검증합니다."""
  current_dir = os.path.dirname(os.path.abspath(__file__))
  skill_dir = os.path.abspath(os.path.join(current_dir, "..", ".agents", "skills", "asset-advisor"))
  skill_md = os.path.join(skill_dir, "SKILL.md")

  assert os.path.exists(skill_md), f"asset-advisor SKILL.md 없음: {skill_md}"

  with open(skill_md, "r", encoding="utf-8") as f:
    content = f.read()

    # 스킬 메타데이터 검증
    assert "name: asset-advisor" in content

    # MCP 도구 사용 규칙 검증
    assert "assetmanager" in content
    assert "get_portfolio_status" in content or "get_asset_summary" in content

    # 공용 레퍼런스 참조 검증
    assert "docs/references/investment-principles.md" in content
    assert "docs/references/trade-cases-index.md" in content
