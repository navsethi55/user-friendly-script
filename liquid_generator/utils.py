"""Shared utility functions for Liquid template generation."""

import re
from html import unescape

TAG_RE = re.compile(r"<[^>]+>")


def strip_html(s):
    """Remove HTML tags and unescape entities."""
    if not s:
        return ""
    s = unescape(s)
    s = TAG_RE.sub("", s)
    return s


def to_app_lang(lang_code):
    """Normalize a language code to appLanguage format (e.g. 'en-GB')."""
    if "-" in lang_code:
        base, region = lang_code.split("-", 1)
        return base.lower() + "-" + region.upper()
    return lang_code.lower()


def starts_with_any(lang_code, prefixes):
    """Check if lang_code starts with any of the given prefixes."""
    return any(lang_code.startswith(p) for p in prefixes)
