"""Applies input, output, and privacy safeguards to the QA workflow."""

import re
import unicodedata

from rest_framework.exceptions import ValidationError


PERSIAN_TRANSLATION = str.maketrans({"ي": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه"})


class TextNormalizer:
    @staticmethod
    def normalize(text):
        text = unicodedata.normalize("NFKC", text or "").translate(PERSIAN_TRANSLATION)
        return re.sub(r"\s+", " ", text).strip()


class PromptSecurityPolicy:
    SUSPICIOUS_PATTERNS = (
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"reveal\s+(the\s+)?system\s+prompt",
        r"developer\s+message",
        r"bypass\s+(security|permissions|authorization)",
        r"دستور(?:های)?\s+قبلی\s+را\s+نادیده",
        r"پرامپت\s+سیستم\s+را\s+نشان",
    )

    @classmethod
    def validate(cls, text):
        normalized = TextNormalizer.normalize(text).lower()
        if any(
            re.search(pattern, normalized, flags=re.IGNORECASE)
            for pattern in cls.SUSPICIOUS_PATTERNS
        ):
            raise ValidationError(
                {
                    "text": "The question contains instructions that cannot be processed safely."
                }
            )
        return normalized


class PIIRedactor:
    EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
    PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
    STUDENT_ID = re.compile(
        r"\b(?:student\s*(?:id|number)|شماره\s*دانشجویی)\s*[:#-]?\s*[A-Z0-9-]{4,}\b",
        re.I,
    )

    @classmethod
    def redact(cls, text):
        text = cls.EMAIL.sub("[REDACTED_EMAIL]", text)
        text = cls.PHONE.sub("[REDACTED_PHONE]", text)
        return cls.STUDENT_ID.sub("[REDACTED_STUDENT_ID]", text)
