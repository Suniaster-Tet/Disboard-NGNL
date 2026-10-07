"""Render Mermaid fences from the project documentation with Mermaid CLI."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ("README.md", "docs/architecture.md")
MERMAID_FENCE = re.compile(r"^```mermaid\s*\n(.*?)^```\s*$", re.MULTILINE | re.DOTALL)


def main() -> int:
    renderer = shutil.which("mmdc")
    if renderer is None:
        print(
            "Mermaid CLI (mmdc) is required. Install it with "
            "`npm install --global @mermaid-js/mermaid-cli@11.4.2`."
        )
        return 2

    failures = 0
    rendered = 0
    with tempfile.TemporaryDirectory(prefix="disboard-mermaid-") as temporary_directory:
        temporary_path = Path(temporary_directory)
        for document in DOCUMENTS:
            markdown = (ROOT / document).read_text(encoding="utf-8")
            blocks = MERMAID_FENCE.findall(markdown)
            if not blocks:
                print(f"FAIL {document}: no Mermaid blocks found")
                failures += 1
                continue

            for block_number, source in enumerate(blocks, start=1):
                input_path = temporary_path / f"diagram-{rendered + 1}.mmd"
                output_path = temporary_path / f"diagram-{rendered + 1}.svg"
                input_path.write_text(source, encoding="utf-8")
                result = subprocess.run(
                    [renderer, "-i", str(input_path), "-o", str(output_path), "--quiet"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode or not output_path.is_file() or output_path.stat().st_size == 0:
                    print(f"FAIL {document} Mermaid block {block_number}")
                    if result.stdout:
                        print(result.stdout.rstrip())
                    if result.stderr:
                        print(result.stderr.rstrip())
                    failures += 1
                    continue
                rendered += 1

    if failures:
        print(f"Mermaid rendering failed: {failures} block(s) invalid; {rendered} rendered.")
        return 1

    print(f"Mermaid rendering passed: {rendered} block(s) rendered to SVG.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
