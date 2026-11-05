"""Extractor local determinista de texto en archivos PDF e identificador de DOIs sin IA."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Union


class PDFExtractor:
    DOI_REGEX = r"10\.\d{4,9}/[-._;()/:A-Z0-9]+"

    def extract_text_and_dois(self, pdf_path: Union[str, Path]) -> Dict[str, Any]:
        """Extrae texto página por página e identifica DOIs semilla."""
        path = Path(pdf_path)
        if not path.exists():
            return {"status": "error", "message": f"PDF not found: {path}"}

        extracted_text: list[str] = []
        dois_found: set[str] = set()

        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            for idx, page in enumerate(reader.pages, 1):
                txt = page.extract_text() or ""
                extracted_text.append(f"--- Page {idx} ---\n{txt}")
                matches = re.findall(self.DOI_REGEX, txt, re.IGNORECASE)
                for m in matches:
                    dois_found.add(m.rstrip("."))

            full_txt = "\n\n".join(extracted_text)
            return {
                "status": "success",
                "pages": len(reader.pages),
                "text": full_txt[:2000],
                "dois": list(dois_found),
            }
        except Exception as e:
            return {"status": "error", "message": f"PDF extraction failed: {e}"}
