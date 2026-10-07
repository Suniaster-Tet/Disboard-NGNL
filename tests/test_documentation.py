import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MERMAID_FENCE = re.compile(r"^```mermaid\s*\n(.*?)^```\s*$", re.MULTILINE | re.DOTALL)
NODE_DECLARATION = re.compile(
    r"(?<![\w])([A-Za-z_][A-Za-z0-9_]*)\s*"
    r"(?:\[([^\]\n]*)\]|\{([^}\n]*)\}|\(\(([^)\n]*)\)\))"
)


class DocumentationDiagramTests(unittest.TestCase):
    def test_mermaid_blocks_are_balanced_and_node_labels_consistent(self):
        for relative_path in ("README.md", "docs/architecture.md"):
            markdown = (ROOT / relative_path).read_text(encoding="utf-8")
            blocks = MERMAID_FENCE.findall(markdown)

            self.assertGreaterEqual(len(blocks), 2, relative_path)
            self.assertEqual(markdown.count("```mermaid"), len(blocks), relative_path)
            for block_number, block in enumerate(blocks, start=1):
                self.assertRegex(
                    block,
                    r"(?m)^\s*(?:flowchart|graph)\s+(?:TD|TB|BT|RL|LR)\s*$",
                )
                labels = {}
                for match in NODE_DECLARATION.finditer(block):
                    node_id = match.group(1)
                    label = next(value for value in match.groups()[1:] if value is not None)
                    previous = labels.setdefault(node_id, label)
                    self.assertEqual(
                        previous,
                        label,
                        f"{relative_path} Mermaid block {block_number} "
                        f"redeclares {node_id!r} with a different label.",
                    )


if __name__ == "__main__":
    unittest.main()
