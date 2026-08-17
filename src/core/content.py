from __future__ import annotations


def build_processed_content(
    *,
    yaml_text: str,
    body_text: str,
    ai_refined: str,
    ai_section_title: str = "### 🤖 AI 자동 요약 및 인덱싱",
    body_section_title: str = "### 본문",
) -> str:
    """Build publish-ready markdown with AI summary and original body."""
    return (
        "---\n"
        f"{yaml_text.strip()}\n"
        "---\n\n"
        f"{ai_section_title}\n"
        f"{(ai_refined or '').strip()}\n\n"
        "---\n\n"
        f"{body_section_title}\n"
        f"{(body_text or '').strip()}"
    )

