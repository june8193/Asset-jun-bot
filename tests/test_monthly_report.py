# -*- coding: utf-8 -*-
"""asset-monthly-report 스킬 구조 및 asset-auditor 연동 검증 테스트 모듈입니다."""

import os
import pytest


def test_asset_monthly_report_skill_structure():
  """asset-monthly-report 스킬 디렉터리 및 SKILL.md 파일이 정상 존재하는지 검증합니다."""
  current_dir = os.path.dirname(os.path.abspath(__file__))
  skill_dir = os.path.abspath(os.path.join(current_dir, "..", ".agents", "skills", "asset-monthly-report"))
  skill_md = os.path.join(skill_dir, "SKILL.md")

  assert os.path.exists(skill_md), f"SKILL.md not found at {skill_md}"

  with open(skill_md, "r", encoding="utf-8") as f:
    content = f.read()

  # 기본 YAML Frontmatter 및 핵심 워크플로우 검증
  assert "name: asset-monthly-report" in content
  assert "reports/asset_monthly" in content
  assert "Asset_monthly_report_" in content
  assert "query_asset.py" in content
  assert "query_market.py" in content
  assert "markdown_to_pdf.py" not in content
  assert "send_telegram.py" in content


def test_all_report_skills_no_pdf():
  """일간/주간/월간 보고서 스킬들에서 PDF 변환 및 markdown_to_pdf.py 참조가 제거되었는지 검증합니다."""
  current_dir = os.path.dirname(os.path.abspath(__file__))
  skills_root = os.path.abspath(os.path.join(current_dir, "..", ".agents", "skills"))
  report_skills = [
      "korea-daily-index-report",
      "korea-weekly-index-report",
      "us-daily-index-report",
      "us-weekly-index-report",
      "asset-monthly-report",
  ]

  for skill_name in report_skills:
    skill_md = os.path.join(skills_root, skill_name, "SKILL.md")
    assert os.path.exists(skill_md), f"{skill_name} SKILL.md not found"
    with open(skill_md, "r", encoding="utf-8") as f:
      skill_content = f.read()
    assert "markdown_to_pdf.py" not in skill_content, f"{skill_name} still references markdown_to_pdf.py"
    assert "PDF" not in skill_content, f"{skill_name} still contains PDF keyword"


def test_asset_auditor_hierarchical_reports_integration():
  """asset-auditor SKILL.md에 미참조 월간/주간/일간 보고서 계층적 로드 및 분석 반영 워크플로우가 명시되어 있는지 검증합니다."""
  current_dir = os.path.dirname(os.path.abspath(__file__))
  auditor_skill_md = os.path.abspath(
      os.path.join(current_dir, "..", ".agents", "skills", "asset-auditor", "SKILL.md")
  )

  assert os.path.exists(auditor_skill_md)

  with open(auditor_skill_md, "r", encoding="utf-8") as f:
    content = f.read()

  # 계층적 보고서(월간, 주간, 일간) 탐색 키워드 검증
  assert "reports/asset_monthly" in content or "Asset_monthly_report_" in content
  assert "weekly" in content
  assert "daily" in content
  assert "계층적" in content or "주간" in content
