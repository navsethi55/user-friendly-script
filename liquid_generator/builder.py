"""
Block builders for generating Liquid conditional templates.

Handles single-market language-only mode, per-country language blocks,
and multi-country registration-country branching.
"""

from collections import defaultdict

from liquid_generator.rules import RULES
from liquid_generator.utils import strip_html, to_app_lang, starts_with_any


# ---------------------------------------------------------------------------
# Condition helpers
# ---------------------------------------------------------------------------

def lang_condition(app_lang, first_lang):
    prefix = "{% if" if first_lang else "{% elsif"
    if app_lang == "fr-FR":
        return (
            "    " + prefix + " "
            "{{custom_attribute.${appLanguage}}} == 'fr-FR' or "
            "{{custom_attribute.${appLanguage}}} == 'fr-CA' %}"
        )
    if app_lang.startswith("en-"):
        return (
            "    " + prefix + " "
            "{{custom_attribute.${appLanguage}}} == 'en' or "
            "{{custom_attribute.${appLanguage}}} == '" + app_lang + "' %}"
        )
    return (
        "    " + prefix + " "
        "{{custom_attribute.${appLanguage}}} == '" + app_lang + "' %}"
    )


# ---------------------------------------------------------------------------
# Single-market (language-only) builder
# ---------------------------------------------------------------------------

def build_single_market_lang_only(country, langs_map, field_name):
    """For exactly one market: emit only appLanguage IF/ELSE."""
    en_text = None
    native_text = None
    else_pref = (RULES.get(country) or {}).get("else_prefix")

    # Prefer en-GB
    for lc, data in langs_map.items():
        if to_app_lang(lc) == "en-GB":
            en_text = strip_html(data.get(field_name, ""))
            break
    # Any en-*
    if en_text is None:
        for lc, data in langs_map.items():
            if to_app_lang(lc).startswith("en"):
                en_text = strip_html(data.get(field_name, ""))
                break

    # Native: exact else_prefix, then first non-en
    if else_pref:
        for lc, data in langs_map.items():
            if lc == else_pref or to_app_lang(lc).startswith(else_pref):
                native_text = strip_html(data.get(field_name, ""))
                break
    if native_text is None:
        for lc, data in langs_map.items():
            if not to_app_lang(lc).startswith("en"):
                native_text = strip_html(data.get(field_name, ""))
                break

    if native_text is None:
        native_text = en_text or ""
    if en_text is None:
        en_text = ""

    return "\n".join([
        "    {% if {{custom_attribute.${appLanguage}}} == 'en' "
        "or {{custom_attribute.${appLanguage}}} == 'en-GB' %}",
        en_text,
        "    {% else %}",
        native_text,
        "    {% endif %}",
    ])


# ---------------------------------------------------------------------------
# Per-country block builder
# ---------------------------------------------------------------------------

def _build_custom_be(langs_map, field_name):
    fr_key = nl_key = en_key = None
    for lc in langs_map:
        lc_norm = to_app_lang(lc)
        if lc_norm == "fr-FR" and fr_key is None:
            fr_key = lc
        if lc_norm == "nl" and nl_key is None:
            nl_key = lc
        if lc_norm == "en-GB" and en_key is None:
            en_key = lc
    if not en_key:
        for lc in langs_map:
            if to_app_lang(lc).startswith("en"):
                en_key = lc
                break

    else_text = strip_html(langs_map.get(en_key, {}).get(field_name, "")) if en_key else ""
    if not fr_key and not nl_key:
        return else_text

    lines = []
    if fr_key:
        lines.append(
            "    {% if {{custom_attribute.${appLanguage}}} == 'fr-FR' "
            "or {{custom_attribute.${appLanguage}}} == 'fr-CA' %}"
        )
        lines.append(strip_html(langs_map[fr_key].get(field_name, "")))
    if nl_key:
        if fr_key:
            lines.append("    {% elsif {{custom_attribute.${appLanguage}}} == 'nl' %}")
        else:
            lines.append("    {% if {{custom_attribute.${appLanguage}}} == 'nl' %}")
        lines.append(strip_html(langs_map[nl_key].get(field_name, "")))
    lines.append("    {% else %}")
    lines.append(else_text)
    lines.append("    {% endif %}")
    return "\n".join(lines)


def _build_custom_lu(langs_map, field_name):
    fr_key = en_key = None

    for lc in langs_map:
        if to_app_lang(lc) == "fr-FR":
            fr_key = lc
            break
    if not fr_key:
        for lc in langs_map:
            if to_app_lang(lc).startswith("fr"):
                fr_key = lc
                break

    for lc in langs_map:
        if to_app_lang(lc) == "en-GB":
            en_key = lc
            break
    if not en_key:
        for lc in langs_map:
            if to_app_lang(lc).startswith("en"):
                en_key = lc
                break

    fr_text = strip_html(langs_map.get(fr_key, {}).get(field_name, "")) if fr_key else ""
    en_text = strip_html(langs_map.get(en_key, {}).get(field_name, "")) if en_key else ""

    if fr_key:
        return "\n".join([
            "    {% if {{custom_attribute.${appLanguage}}} == 'fr-FR' "
            "or {{custom_attribute.${appLanguage}}} == 'fr-CA' %}",
            fr_text,
            "    {% else %}",
            en_text,
            "    {% endif %}",
        ])
    return en_text


def _build_custom_fi(langs_map, field_name):
    fi_key = en_key = None

    for lc in langs_map:
        if to_app_lang(lc).startswith("fi"):
            fi_key = lc
            break

    for lc in langs_map:
        if to_app_lang(lc) == "en-GB":
            en_key = lc
            break
    if not en_key:
        for lc in langs_map:
            if to_app_lang(lc).startswith("en"):
                en_key = lc
                break

    fi_text = strip_html(langs_map.get(fi_key, {}).get(field_name, "")) if fi_key else ""
    en_text = strip_html(langs_map.get(en_key, {}).get(field_name, "")) if en_key else ""

    return "\n".join([
        "    {% if {{custom_attribute.${appLanguage}}} == 'en' "
        "or {{custom_attribute.${appLanguage}}} == 'en-GB' %}",
        en_text,
        "    {% else %}",
        fi_text,
        "    {% endif %}",
    ])


def build_country_block(country, langs_map, field_name):
    """Build Liquid conditionals for a single country's languages."""
    rule = RULES.get(country, {})

    if rule.get("custom_be"):
        return _build_custom_be(langs_map, field_name)
    if rule.get("custom_lu"):
        return _build_custom_lu(langs_map, field_name)
    if rule.get("custom_fi"):
        return _build_custom_fi(langs_map, field_name)

    # Static (IE, IS, UK, etc.)
    if "static_lang" in rule:
        static_key = None
        for lc in langs_map:
            if to_app_lang(lc) == to_app_lang(rule["static_lang"]):
                static_key = lc
                break
        if not static_key and langs_map:
            static_key = next(iter(langs_map))
        return strip_html(langs_map.get(static_key, {}).get(field_name, ""))

    # Generic language branching
    if not langs_map:
        return ""

    all_langs = list(langs_map.keys())
    if "only_explicit_prefixes" in rule:
        explicit = [lc for lc in all_langs if starts_with_any(lc, rule["only_explicit_prefixes"])]
    elif "suppress_prefixes" in rule:
        explicit = [lc for lc in all_langs if not starts_with_any(lc, rule["suppress_prefixes"])]
    else:
        explicit = all_langs[:]

    def sort_key(k):
        return (0 if k.startswith("en") else 1, to_app_lang(k))

    explicit_sorted = sorted(explicit, key=sort_key)

    lines = []
    if explicit_sorted:
        first_lang = True
        for lang_code in explicit_sorted:
            app_lang = to_app_lang(lang_code)
            lines.append(lang_condition(app_lang, first_lang))
            first_lang = False
            lines.append(strip_html(langs_map[lang_code].get(field_name, "")))

        else_text = None
        else_pref = rule.get("else_prefix")
        if else_pref:
            chosen = None
            for lc in all_langs:
                if lc == else_pref:
                    chosen = lc
                    break
            if not chosen:
                for lc in all_langs:
                    if lc.startswith(else_pref):
                        chosen = lc
                        break
            if chosen:
                else_text = strip_html(langs_map[chosen].get(field_name, ""))
        if else_text is None and all_langs:
            chosen_any = sorted(all_langs, key=sort_key)[0]
            else_text = strip_html(langs_map[chosen_any].get(field_name, ""))

        lines += ["    {% else %}", else_text or "", "    {% endif %}"]
    else:
        if all_langs:
            chosen_any = sorted(all_langs, key=sort_key)[0]
            lines.append(strip_html(langs_map[chosen_any].get(field_name, "")))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Final fallback picker
# ---------------------------------------------------------------------------

def pick_final_fallback(grouped, field_name):
    """Pick fallback text: prefer UK en-gb -> any en-gb -> any en-* -> any."""
    if "UK" in grouped:
        for lc in grouped["UK"]:
            if to_app_lang(lc) == "en-GB":
                return grouped["UK"][lc].get(field_name, "")
    for _, langmap in grouped.items():
        for lc in langmap:
            if to_app_lang(lc) == "en-GB":
                return langmap[lc].get(field_name, "")
    for _, langmap in grouped.items():
        for lc in langmap:
            if to_app_lang(lc).startswith("en"):
                return langmap[lc].get(field_name, "")
    for _, langmap in grouped.items():
        any_lc = next(iter(langmap))
        return langmap[any_lc].get(field_name, "")
    return ""


# ---------------------------------------------------------------------------
# Top-level Liquid renderer
# ---------------------------------------------------------------------------

def build_liquid_from_grouped(grouped, field_name):
    """
    Build the full Liquid template from a grouped dict.

    If only one country: emit language-only conditionals.
    If multiple: emit registrationCountry branching with nested language blocks.
    """
    countries = sorted(grouped.keys())
    if not countries:
        return ""

    # Single-market: language-only mode
    if len(countries) == 1:
        country = countries[0]
        return build_single_market_lang_only(country, grouped[country], field_name)

    # Multi-country branching
    lines = []
    first_country = True
    for country in countries:
        if country == "UK":
            cond = (
                ("{% if" if first_country else "{% elsif") + " "
                "{{custom_attribute.${registrationCountry}}} == 'GB' or "
                "{{custom_attribute.${registrationCountry}}} == 'UK' %}"
            )
        else:
            cond = (
                ("{% if" if first_country else "{% elsif") + " "
                "{{custom_attribute.${registrationCountry}}} == '" + country + "' %}"
            )
        lines.append(cond)
        first_country = False
        lines.append(build_country_block(country, grouped[country], field_name))

    fallback_text = pick_final_fallback(grouped, field_name)
    lines += ["{% else %}", fallback_text or "", "{% endif %}"]
    return "\n".join(lines)
