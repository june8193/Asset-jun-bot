# -*- coding: utf-8 -*-
"""asset-auditor 스킬 무결성 검증 테스트 모듈입니다."""

import os
import pytest


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


