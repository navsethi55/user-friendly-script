"""
Country-language rules for Liquid template generation.

Each country maps to a dict describing how to handle its languages:
  - static_lang:              Use a single language, no conditionals.
  - else_prefix:              Language prefix for the {% else %} branch.
  - suppress_prefixes:        Language prefixes to exclude from explicit {% if/elsif %} conditions.
  - only_explicit_prefixes:   Only these prefixes get explicit conditions; others go to else.
  - custom_be / custom_lu / custom_fi:  Flags for country-specific logic.
"""

RULES = {
    # German-speaking markets
    "AT": {"else_prefix": "de", "only_explicit_prefixes": ["en"]},
    "DE": {"else_prefix": "de", "only_explicit_prefixes": ["en"]},
    "CH": {"else_prefix": "de", "suppress_prefixes": ["de"]},

    # Belgium: FR -> NL -> EN-GB fallback
    "BE": {"custom_be": True},

    # Nordic / Southern Europe
    "DK": {"else_prefix": "da", "suppress_prefixes": ["da"]},
    "ES": {"else_prefix": "es", "suppress_prefixes": ["es"]},
    "FI": {"custom_fi": True},
    "FR": {"else_prefix": "fr", "suppress_prefixes": ["fr"]},
    "GR": {"else_prefix": "el", "suppress_prefixes": ["el"]},

    # English-only (static en-gb)
    "IE": {"static_lang": "en-gb"},
    "IS": {"static_lang": "en-gb"},
    "BG": {"static_lang": "en-gb"},
    "RS": {"static_lang": "en-gb"},
    "HR": {"static_lang": "en-gb"},
    "SI": {"static_lang": "en-gb"},
    "BA": {"static_lang": "en-gb"},
    "AL": {"static_lang": "en-gb"},
    "MK": {"static_lang": "en-gb"},
    "ME": {"static_lang": "en-gb"},
    "MT": {"static_lang": "en-gb"},
    "LT": {"static_lang": "en-gb"},
    "LV": {"static_lang": "en-gb"},
    "EE": {"static_lang": "en-gb"},
    "UK": {"static_lang": "en-gb"},

    # Other European markets
    "IT": {"else_prefix": "it", "suppress_prefixes": ["it"]},
    "LU": {"custom_lu": True},
    "NL": {"else_prefix": "nl", "suppress_prefixes": ["nl"]},
    "NO": {"else_prefix": "no", "suppress_prefixes": ["no"]},
    "PL": {"else_prefix": "pl", "suppress_prefixes": ["pl"]},
    "PT": {"else_prefix": "pt", "suppress_prefixes": ["pt"]},
    "SE": {"else_prefix": "sv", "suppress_prefixes": ["sv"]},
    "TR": {"else_prefix": "tr", "suppress_prefixes": ["tr"]},

    # Central/Eastern Europe
    "CZ": {"else_prefix": "cs", "suppress_prefixes": ["cs"]},
    "HU": {"else_prefix": "hu", "suppress_prefixes": ["hu"]},
    "RO": {"else_prefix": "ro", "suppress_prefixes": ["ro"]},
    "SK": {"else_prefix": "sk", "suppress_prefixes": ["sk"]},
}
