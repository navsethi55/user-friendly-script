"""
Main processing logic: reads a JSON structure and produces Liquid template outputs.

Returns a list of (filename, liquid_content) tuples instead of writing to disk,
so callers (web UI, CLI) can decide what to do with the results.
"""

import json
import re
from collections import defaultdict

from liquid_generator.utils import strip_html
from liquid_generator.builder import build_liquid_from_grouped


# ---------------------------------------------------------------------------
# Grouper helpers
# ---------------------------------------------------------------------------

def group_for_block(copy_block, field_name):
    """Group a Copy block (locale_key -> {field: value}) by country."""
    grouped = defaultdict(dict)
    for locale_key, fields in (copy_block or {}).items():
        if "_" not in locale_key:
            continue
        val = strip_html((fields.get(field_name) or "").strip()) if isinstance(fields, dict) else ""
        if not val:
            continue
        country, lang = locale_key.split("_", 1)
        grouped[country][lang] = {field_name: val}
    return grouped


def group_for_map(locale_map, field_name):
    """Group a flat locale->string map by country."""
    grouped = defaultdict(dict)
    for locale_key, val in (locale_map or {}).items():
        if "_" not in locale_key:
            continue
        val = strip_html((val or "").strip())
        if not val:
            continue
        country, lang = locale_key.split("_", 1)
        grouped[country][lang] = {field_name: val}
    return grouped


def group_for_cta_map(locale_map, subfield):
    """Extract 'label' or 'link' from cta maps (locale -> {link, label})."""
    grouped = defaultdict(dict)
    for locale_key, val in (locale_map or {}).items():
        if "_" not in locale_key or not isinstance(val, dict):
            continue
        subval = val.get(subfield)
        if not subval:
            continue
        country, lang = locale_key.split("_", 1)
        grouped[country][lang] = {subfield: strip_html(str(subval).strip())}
    return grouped


# ---------------------------------------------------------------------------
# Main processor
# ---------------------------------------------------------------------------

def process_json(data):
    """
    Process a parsed JSON dict and return generated Liquid templates.

    Args:
        data: The parsed JSON object (expects data["a"]["modules"][0]["content"]).

    Returns:
        A dict mapping filename -> liquid_content for all generated files.
        Also returns a list of skipped filenames (fields with no data).
    """
    content = data["a"]["modules"][0]["content"]

    tasks = []  # list of (out_filename, grouped_map, fieldname)

    # 1) Standard: content.Copy -> per-locale objects with headline/body
    std_copy = content.get("Copy")
    if isinstance(std_copy, dict):
        for fname in ["headline", "body"]:
            has_any = any(
                isinstance(v, dict) and strip_html(str(v.get(fname, ""))).strip()
                for v in std_copy.values()
            )
            if has_any:
                grouped = defaultdict(dict)
                for loc, perfield in std_copy.items():
                    if "_" not in loc:
                        continue
                    val = strip_html(str(perfield.get(fname, "")).strip())
                    if not val:
                        continue
                    c, l = loc.split("_", 1)
                    grouped[c][l] = {fname: val}
                tasks.append((fname + ".liquid", grouped, fname))

    # 2) Modal: flat maps for headline/body/dismiss + cta.label
    modal_sources = {
        "headline": content.get("headline"),
        "body": content.get("body"),
        "dismiss": content.get("dismiss"),
        "cta": (content.get("cta") or {}).get("label"),
    }
    for fname, fmap in modal_sources.items():
        if isinstance(fmap, dict) and any(strip_html(str(v)).strip() for v in fmap.values()):
            tasks.append((fname + ".liquid", group_for_map(fmap, fname), fname))

    # 3) Push blocks: Copy_0..Copy_6
    push_blocks = {
        "Copy_0": ["android_headline", "android_body", "ios_headline", "ios_body"],
        "Copy_1": ["headline_1", "body_1"],
        "Copy_2": ["headline_2", "body_2"],
        "Copy_3": ["headline_3", "body_3"],
        "Copy_4": ["headline_4", "body_4"],
        "Copy_5": ["headline_5", "body_5"],
        "Copy_6": ["headline_6", "body_6"],
    }
    for block, fields in push_blocks.items():
        blk = content.get(block)
        if not isinstance(blk, dict):
            continue
        for fname in fields:
            if any(
                isinstance(v, dict) and strip_html(str(v.get(fname, ""))).strip()
                for v in blk.values()
            ):
                tasks.append((fname + ".liquid", group_for_block(blk, fname), fname))

    # 4) Numbered top-level keys: headline_1, body_1, cta_1, etc.
    num_key_re = re.compile(r"^(headline|body|dismiss|cta)_(\d+)$", re.IGNORECASE)
    for key, val in content.items():
        m = num_key_re.match(key)
        if not m:
            continue
        base = m.group(1).lower()
        idx = m.group(2)

        if base in ("headline", "body", "dismiss"):
            if isinstance(val, dict) and any(strip_html(str(v)).strip() for v in val.values()):
                out_name = f"{base}_{idx}.liquid"
                tasks.append((out_name, group_for_map(val, f"{base}_{idx}"), f"{base}_{idx}"))

        elif base == "cta":
            if isinstance(val, dict):
                label_grouped = group_for_cta_map(val, "label")
                if any(label_grouped.values()):
                    tasks.append((f"cta_{idx}_label.liquid", label_grouped, "label"))
                link_grouped = group_for_cta_map(val, "link")
                if any(link_grouped.values()):
                    tasks.append((f"cta_{idx}_link.liquid", link_grouped, "link"))

    # Non-numbered CTA object maps
    cta_val = content.get("cta")
    if isinstance(cta_val, dict) and any(isinstance(v, dict) for v in cta_val.values()):
        label_grouped = group_for_cta_map(cta_val, "label")
        if any(label_grouped.values()):
            tasks.append(("cta_label.liquid", label_grouped, "label"))
        link_grouped = group_for_cta_map(cta_val, "link")
        if any(link_grouped.values()):
            tasks.append(("cta_link.liquid", link_grouped, "link"))

    # Generate output
    written = {}
    skipped = []
    for out_file, grouped, field_name in tasks:
        liquid = build_liquid_from_grouped(grouped, field_name)
        if liquid.strip():
            written[out_file] = liquid
        else:
            skipped.append(out_file)

    return written, skipped
