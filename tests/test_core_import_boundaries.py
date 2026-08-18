from pathlib import Path

FORBIDDEN_IMPORT_SNIPPETS = (
    "from src.core",
    "import src.core",
)


def test_no_src_core_imports_in_app_code() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [repo_root / "src", repo_root / "harvest_flow"]
    offenders: list[str] = []

    for target in targets:
        for path in target.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if any(token in text for token in FORBIDDEN_IMPORT_SNIPPETS):
                offenders.append(str(path.relative_to(repo_root)))

    assert not offenders, (
        f"Replace private core imports with harvest_flow_core API: {offenders}"
    )
