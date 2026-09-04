from __future__ import annotations

import re
from pathlib import Path

LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    missing: list[str] = []
    for document in sorted(root.rglob("*.md")):
        for match in LINK.finditer(document.read_text(encoding="utf-8")):
            target = match.group(1).split("#", maxsplit=1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (document.parent / target).resolve().exists():
                missing.append(f"{document.relative_to(root)} -> {target}")
    if missing:
        print("Missing local documentation links:")
        print("\n".join(missing))
        return 1
    print("All local documentation links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
