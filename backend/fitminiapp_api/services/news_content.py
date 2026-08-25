from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
HTTPS_URL_PATTERN = re.compile(r"https://[^\s<>]+")
COMPACT_HEADER_PATTERN = re.compile(r"(?m)^(ЗАГОЛОВОК|КРАТКО|ПОЧЕМУ ЭТО ВАЖНО|ИСТОЧНИК)\s*$")


@dataclass(frozen=True)
class EditorialContent:
    headline: str
    summary: str
    why_it_matters: str
    source_url: str

    def fields(self) -> dict[str, str]:
        return {
            "headline": self.headline,
            "summary": self.summary,
            "why_it_matters": self.why_it_matters,
        }


def _trusted_https_url(value: str) -> str | None:
    match = HTTPS_URL_PATTERN.search(value)
    if match is None:
        return None
    url = match.group(0).rstrip('.,;:!?)"]}')
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    return url


def _valid_content(content: EditorialContent) -> bool:
    return bool(
        1 <= len(content.headline) <= 180
        and 1 <= len(content.summary) <= 1200
        and len(content.why_it_matters) <= 320
        and CYRILLIC_PATTERN.search(content.headline)
        and CYRILLIC_PATTERN.search(content.summary)
        and (not content.why_it_matters or CYRILLIC_PATTERN.search(content.why_it_matters))
        and _trusted_https_url(content.source_url) == content.source_url
    )


def _compact_content(text: str) -> EditorialContent | None:
    matches = list(COMPACT_HEADER_PATTERN.finditer(text))
    labels = [match.group(1) for match in matches]
    if (
        not matches
        or labels.count("ЗАГОЛОВОК") != 1
        or labels.count("КРАТКО") != 1
        or labels.count("ИСТОЧНИК") != 1
        or labels.count("ПОЧЕМУ ЭТО ВАЖНО") > 1
        or labels[0] != "ЗАГОЛОВОК"
        or labels[1] != "КРАТКО"
        or labels[-1] != "ИСТОЧНИК"
    ):
        return None
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        value = text[match.end() : end].strip().strip("─").strip()
        sections[match.group(1)] = value
    source_url = _trusted_https_url(sections["ИСТОЧНИК"])
    if source_url is None:
        return None
    content = EditorialContent(
        headline=" ".join(sections["ЗАГОЛОВОК"].split()),
        summary="\n\n".join(
            " ".join(paragraph.split())
            for paragraph in re.split(r"\n\s*\n", sections["КРАТКО"])
            if paragraph.strip()
        ),
        why_it_matters=" ".join(sections.get("ПОЧЕМУ ЭТО ВАЖНО", "").split()),
        source_url=source_url,
    )
    return content if _valid_content(content) else None


def _legacy_section(text: str, start: str, ends: tuple[str, ...]) -> str:
    start_match = re.search(rf"(?m)^{re.escape(start)}\s*$", text)
    if start_match is None:
        return ""
    end_positions = [
        match.start()
        for marker in ends
        if (match := re.search(rf"(?m)^{re.escape(marker)}\s*$", text[start_match.end() :]))
        is not None
    ]
    end = start_match.end() + min(end_positions) if end_positions else len(text)
    return text[start_match.end() : end].strip()


def _legacy_content(text: str) -> EditorialContent | None:
    headline_match = re.search(r"(?m)^Заголовок:\s*(.+)$", text)
    source_url = _trusted_https_url(text)
    if headline_match is None or source_url is None:
        return None
    summary = _legacy_section(
        text,
        "Что произошло",
        ("Почему это важно", "Как применять / что не меняется", "Ограничения"),
    )
    why = _legacy_section(
        text,
        "Почему это важно",
        ("Как применять / что не меняется", "Ограничения"),
    )
    content = EditorialContent(
        headline=" ".join(headline_match.group(1).split()),
        summary=" ".join(summary.split()),
        why_it_matters=" ".join(why.split())[:320],
        source_url=source_url,
    )
    return content if _valid_content(content) else None


def parse_editorial_content(text: str) -> EditorialContent | None:
    clean_text = text.strip()
    return _compact_content(clean_text) or _legacy_content(clean_text)


def editorial_content_from_metadata(
    metadata: dict,
    *,
    fallback_text: str,
) -> EditorialContent | None:
    fields = metadata.get("editorial_fields")
    source_url = metadata.get("trusted_source_url")
    if isinstance(fields, dict) and isinstance(source_url, str):
        content = EditorialContent(
            headline=str(fields.get("headline", "")).strip(),
            summary=str(fields.get("summary", "")).strip(),
            why_it_matters=str(fields.get("why_it_matters", "")).strip(),
            source_url=source_url.strip(),
        )
        if _valid_content(content):
            return content
    return parse_editorial_content(fallback_text)
