import ast
from pathlib import Path

ROOT = Path(__file__).parent.parent
TEXT_CALLS = {"read_text", "write_text"}


def calls_without_encoding(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        f"{path.relative_to(ROOT)}:{node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in TEXT_CALLS
        and not any(k.arg == "encoding" for k in node.keywords)
    ]


def test_every_text_read_and_write_names_its_encoding() -> None:
    files = [*ROOT.glob("src/**/*.py"), *ROOT.glob("scripts/*.py"), *ROOT.glob("tests/*.py")]
    assert [call for f in sorted(files) for call in calls_without_encoding(f)] == []
