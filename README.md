# Liquid Template Generator

A user-friendly tool for generating multi-market, multi-language Liquid templates from JSON content files.

Auto-detects content format (Standard / Modal / Push) and produces `.liquid` files with the correct `registrationCountry` and `appLanguage` conditionals for each market.

## Quick Start

### Install dependencies

```bash
pip install -r requirements.txt
```

### Web UI (Streamlit)

```bash
streamlit run app.py
```

Then open the URL shown in your terminal (typically `http://localhost:8501`). From the web interface you can:

1. **Upload** your JSON content file
2. **Generate** Liquid templates with one click
3. **Preview** each generated file in-browser
4. **Download** individual files or a ZIP of everything

### Command Line

```bash
# Generate .liquid files in the current directory
python cli.py input.json

# Write to a specific output directory
python cli.py input.json -o output/

# Preview without writing files
python cli.py input.json --preview
```

## How It Works

The tool reads JSON content structured as:

```json
{
  "a": {
    "modules": [
      {
        "content": { ... }
      }
    ]
  }
}
```

It auto-detects which content fields are present and generates a `.liquid` file for each one. Supported content shapes:

| Shape | Content keys | Output files |
|-------|-------------|--------------|
| **Standard** | `Copy` (with `headline`, `body`) | `headline.liquid`, `body.liquid` |
| **Modal** | `headline`, `body`, `dismiss`, `cta` | One file per field |
| **Push** | `Copy_0`..`Copy_6` (with platform-specific fields) | e.g. `android_headline.liquid` |
| **Numbered** | `headline_1`, `body_2`, `cta_1`, etc. | e.g. `headline_1.liquid`, `cta_1_label.liquid` |

### Single-market mode

If a field has content for exactly **one** market, the generator emits language-only Liquid (no country check):

```liquid
{% if {{custom_attribute.${appLanguage}}} == 'en' or {{custom_attribute.${appLanguage}}} == 'en-GB' %}
EN_TEXT
{% else %}
NATIVE_TEXT
{% endif %}
```

### Multi-market mode

When multiple markets exist, the output branches on `registrationCountry` first, then `appLanguage` within each country.

## Country Rules

Rules are defined in `liquid_generator/rules.py`. Each country maps to a configuration that controls how language conditionals are generated:

- **Static** (e.g. UK, IE): Single language, no conditionals
- **Custom** (BE, FI, LU): Country-specific branching logic
- **Generic** (DE, FR, ES, etc.): Standard IF/ELSIF/ELSE with configurable `else_prefix` and `suppress_prefixes`

## Project Structure

```
.
├── app.py                      # Streamlit web UI
├── cli.py                      # Command-line interface
├── requirements.txt
└── liquid_generator/
    ├── __init__.py
    ├── rules.py                # Country-language rules
    ├── utils.py                # HTML stripping, lang normalization
    ├── builder.py              # Liquid conditional block builders
    └── processor.py            # JSON parsing and orchestration
```
