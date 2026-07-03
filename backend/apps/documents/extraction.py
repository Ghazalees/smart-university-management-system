"""Safe, dependency-light text extraction for governed knowledge uploads."""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from django.conf import settings
from rest_framework.exceptions import ValidationError

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".pdf",
    ".docx",
    ".docm",
    ".html",
    ".htm",
}

_WORD_XML_PARTS = (
    "word/document.xml",
    "word/header",
    "word/footer",
    "word/footnotes.xml",
    "word/endnotes.xml",
    "word/comments.xml",
)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str):
        value = " ".join(data.split())
        if value:
            self.parts.append(value)

    def text(self) -> str:
        return "\n".join(self.parts)


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "cp1256", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValidationError({"file": "The file text encoding could not be read."})


def _extract_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - installed in normal builds
        raise ValidationError(
            {
                "file": "PDF support is unavailable. Install the backend requirements and try again."
            }
        ) from exc

    try:
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(f"Page {index}\n{text}")
    except Exception as exc:
        raise ValidationError(
            {"file": "The PDF is damaged, encrypted, or cannot be read."}
        ) from exc

    if not pages:
        raise ValidationError(
            {
                "file": "No readable text was found in the PDF. Scanned PDFs require OCR before upload."
            }
        )
    return "\n\n".join(pages)


def _word_part_names(archive: zipfile.ZipFile) -> list[str]:
    """Return relevant Word XML parts in a stable, human-readable order."""

    available = set(archive.namelist())
    names: list[str] = []
    if "word/document.xml" in available:
        names.append("word/document.xml")

    for prefix in ("word/header", "word/footer"):
        names.extend(
            sorted(
                name
                for name in available
                if name.startswith(prefix) and name.endswith(".xml")
            )
        )

    for name in ("word/footnotes.xml", "word/endnotes.xml", "word/comments.xml"):
        if name in available:
            names.append(name)
    return names


def _extract_word_xml_part(xml: bytes) -> list[str]:
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise ValidationError(
            {"file": "The Word document structure is invalid."}
        ) from exc

    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{namespace}p"):
        parts: list[str] = []
        for node in paragraph.iter():
            local_name = node.tag.rsplit("}", 1)[-1]
            if local_name in {"t", "instrText", "delText"} and node.text:
                parts.append(node.text)
            elif local_name == "tab":
                parts.append("\t")
            elif local_name in {"br", "cr"}:
                parts.append("\n")
        value = "".join(parts)
        value = re.sub(r"[ \t]+", " ", value)
        value = re.sub(r" *\n *", "\n", value).strip()
        if value:
            paragraphs.append(value)
    return paragraphs


def _extract_docx(data: bytes) -> str:
    """Extract body, tables, headers, footers, notes and comments from Word Open XML."""

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            part_names = _word_part_names(archive)
            if not part_names:
                raise KeyError("word/document.xml")
            sections: list[str] = []
            for name in part_names:
                paragraphs = _extract_word_xml_part(archive.read(name))
                if not paragraphs:
                    continue
                # The main body remains unlabelled; auxiliary parts get a small heading
                # so their text is searchable without polluting ordinary documents.
                if name != "word/document.xml":
                    label = Path(name).stem.replace("_", " ").title()
                    sections.append(f"{label}\n" + "\n\n".join(paragraphs))
                else:
                    sections.append("\n\n".join(paragraphs))
    except (KeyError, zipfile.BadZipFile) as exc:
        raise ValidationError(
            {
                "file": "The Word file is damaged, is not a valid DOCX/DOCM file, or cannot be read."
            }
        ) from exc

    text = "\n\n".join(sections).strip()
    if not text:
        raise ValidationError({"file": "No readable text was found in the Word file."})
    return text


def _extract_csv(data: bytes) -> str:
    decoded = _decode_text(data)
    try:
        rows = csv.reader(io.StringIO(decoded))
        normalized = [" | ".join(cell.strip() for cell in row) for row in rows]
    except csv.Error as exc:
        raise ValidationError({"file": "The CSV file is invalid."}) from exc
    return "\n".join(row for row in normalized if row.strip())


def _extract_json(data: bytes) -> str:
    try:
        payload = json.loads(_decode_text(data))
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValidationError({"file": "The JSON file is invalid."}) from exc
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _extract_html(data: bytes) -> str:
    parser = _HTMLTextExtractor()
    try:
        parser.feed(_decode_text(data))
    except Exception as exc:
        raise ValidationError({"file": "The HTML file could not be read."}) from exc
    return parser.text()


def _normalize_extracted_text(text: str) -> str:
    text = (
        text.replace("\x00", "")
        .replace("\u00ad", "")
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .replace("\u00a0", " ")
    )
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def extract_uploaded_text(uploaded_file) -> str:
    """Return normalized text from a supported uploaded knowledge file."""

    if not uploaded_file:
        raise ValidationError({"file": "Choose a file to upload."})

    filename = Path(uploaded_file.name or "upload").name
    extension = Path(filename).suffix.lower()
    if extension == ".doc":
        raise ValidationError(
            {
                "file": "Legacy .doc files are not supported. Open the file in Word and save it as .docx, then upload it again."
            }
        )
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValidationError(
            {"file": f"Unsupported file type. Supported types: {supported}."}
        )

    max_bytes = int(getattr(settings, "DOCUMENT_UPLOAD_MAX_BYTES", 5 * 1024 * 1024))
    if uploaded_file.size > max_bytes:
        raise ValidationError(
            {
                "file": f"The file is too large. Maximum size is {max_bytes // (1024 * 1024)} MB."
            }
        )

    data = uploaded_file.read()
    if not data:
        raise ValidationError({"file": "The uploaded file is empty."})

    if extension == ".pdf":
        text = _extract_pdf(data)
    elif extension in {".docx", ".docm"}:
        text = _extract_docx(data)
    elif extension == ".csv":
        text = _extract_csv(data)
    elif extension == ".json":
        text = _extract_json(data)
    elif extension in {".html", ".htm"}:
        text = _extract_html(data)
    else:
        text = _decode_text(data)

    text = _normalize_extracted_text(text)
    if not text:
        raise ValidationError(
            {"file": "No readable text was found in the uploaded file."}
        )

    max_chars = int(getattr(settings, "DOCUMENT_MAX_EXTRACTED_CHARS", 1_000_000))
    if len(text) > max_chars:
        raise ValidationError(
            {
                "file": f"The extracted text is too long. Maximum length is {max_chars:,} characters."
            }
        )
    return text
