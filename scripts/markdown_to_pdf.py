# -*- coding: utf-8 -*-
"""마크다운 파일을 프리미엄 스타일의 PDF로 변환하는 스크립트.

이 스크립트는 Markdown 문서를 HTML로 파싱한 뒤, 외부 CSS 파일과 
맑은 고딕 한글 폰트를 결합하여 고품질의 PDF 파일로 변환합니다.
Windows 환경의 임시 파일 생성 권한 오류를 우회하기 위한 패치가 적용되어 있습니다.
"""

import os
import sys
import shutil
import argparse
import markdown
from xhtml2pdf import pisa
from xhtml2pdf.files import pisaFileObject

# Windows 환경의 xhtml2pdf 임시 파일 권한 오류(PermissionError)를 회피하기 위한 몽키 패치
pisaFileObject.getNamedFile = lambda self: self.uri


def prepare_fonts(font_dir: str):
    """윈도우 시스템 폰트를 지정된 디렉토리로 복사하여 로컬에서 사용하도록 준비합니다.

    Args:
        font_dir: 폰트 파일이 저장될 로컬 디렉토리 경로.
    """
    system_font_normal = "C:/Windows/Fonts/malgun.ttf"
    system_font_bold = "C:/Windows/Fonts/malgunbd.ttf"
    
    os.makedirs(font_dir, exist_ok=True)
    
    local_font_normal = os.path.join(font_dir, "malgun.ttf")
    local_font_bold = os.path.join(font_dir, "malgunbd.ttf")
    
    # 일반 맑은 고딕 폰트 복사
    if not os.path.exists(local_font_normal):
        try:
            print("Copying Malgun Gothic normal font...")
            shutil.copy(system_font_normal, local_font_normal)
        except Exception as e:
            print(f"Warning: Failed to copy normal font: {e}")
            
    # 볼드 맑은 고딕 폰트 복사
    if not os.path.exists(local_font_bold):
        try:
            print("Copying Malgun Gothic bold font...")
            shutil.copy(system_font_bold, local_font_bold)
        except Exception as e:
            print(f"Warning: Failed to copy bold font: {e}")


def convert_md_to_pdf(md_path: str, pdf_path: str, css_path: str, font_dir: str) -> int:
    """마크다운 파일을 HTML로 변환한 후 CSS 스타일과 폰트를 입혀 PDF로 렌더링합니다.

    Args:
        md_path: 입력할 마크다운 파일 경로.
        pdf_path: 출력할 PDF 파일 경로.
        css_path: 적용할 외부 CSS 파일 경로.
        font_dir: 폰트 파일이 복사되어 있는 로컬 디렉토리 경로.

    Returns:
        int: 변환 오류 발생 시의 에러 코드 (성공 시 0).
    """
    # 1. 마크다운 파일 읽기
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 2. 마크다운 -> HTML 변환 (Gfm과 호환되는 tables 확장 기능 포함)
    html_body = markdown.markdown(md_content, extensions=['tables'])
    
    # 3. 폰트 경로 절대 경로로 획득 (xhtml2pdf 파서 호환을 위해 슬래시로 변환)
    abs_font_normal = os.path.abspath(os.path.join(font_dir, "malgun.ttf")).replace("\\", "/")
    abs_font_bold = os.path.abspath(os.path.join(font_dir, "malgunbd.ttf")).replace("\\", "/")
    
    # 4. 외부 CSS 파일 읽기
    css_content = ""
    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
    else:
        print(f"Warning: CSS file not found at {css_path}. Using minimal default styles.")
        
    # 5. 동적 폰트 페이스와 CSS 병합
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            /* 동적 한글 폰트 바인딩 */
            @font-face {{
                font-family: 'MalgunGothic';
                src: url('{abs_font_normal}');
            }}
            @font-face {{
                font-family: 'MalgunGothic';
                src: url('{abs_font_bold}');
                font-weight: bold;
            }}
            
            /* 외부 CSS 스타일 적용 */
            {css_content}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """
    
    # 6. PDF 파일 생성
    with open(pdf_path, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(full_html, dest=pdf_file)
        
    return pisa_status.err


def main():
    """스크립트의 진입점 역할을 수행하며 CLI 인자를 처리합니다."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    
    parser = argparse.ArgumentParser(description="Convert Markdown to premium PDF (Korean Malgun Gothic support)")
    parser.add_argument("input", nargs="?", default=os.path.join(project_dir, "work", "sample_report.md"),
                        help="Path to the input Markdown file")
    parser.add_argument("output", nargs="?", default=os.path.join(project_dir, "work", "sample_report.pdf"),
                        help="Path to the output PDF file")
    parser.add_argument("--css", default=os.path.join(script_dir, "pdf_style.css"),
                        help="Path to the custom CSS template file")
    parser.add_argument("--font-dir", default=os.path.join(script_dir, "fonts"),
                        help="Directory to store and load font files")
    
    args = parser.parse_args()
    
    # 폰트 파일 복사 및 검증
    prepare_fonts(args.font_dir)
    
    print(f"Converting: {args.input} -> {args.output}")
    print(f"Using style: {args.css}")
    
    err = convert_md_to_pdf(args.input, args.output, args.css, args.font_dir)
    if not err:
        print("PDF conversion completed successfully!")
        sys.exit(0)
    else:
        print(f"PDF conversion failed with error code: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
