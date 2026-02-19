"""
Liquid Template Generator - Streamlit Web UI

A user-friendly interface for generating multi-market, multi-language
Liquid templates from JSON content files.

Run with: streamlit run app.py
"""

import io
import json
import zipfile

import streamlit as st

from liquid_generator.processor import process_json
from liquid_generator.rules import RULES

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Liquid Template Generator",
    page_icon="</>",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar: rules reference
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Country Rules Reference")
    st.caption("These rules control how language conditions are generated for each market.")

    # Categorize rules for display
    static_countries = sorted(c for c, r in RULES.items() if "static_lang" in r)
    custom_countries = sorted(c for c, r in RULES.items()
                              if any(k.startswith("custom_") for k in r))
    generic_countries = sorted(c for c in RULES
                               if c not in static_countries and c not in custom_countries)

    with st.expander(f"Static language ({len(static_countries)} markets)", expanded=False):
        st.markdown("These markets use a single language with no conditionals.")
        for c in static_countries:
            st.code(f"{c}: {RULES[c]['static_lang']}", language=None)

    with st.expander(f"Custom logic ({len(custom_countries)} markets)", expanded=False):
        st.markdown("These markets have special branching logic.")
        for c in custom_countries:
            flags = [k for k in RULES[c] if k.startswith("custom_")]
            st.code(f"{c}: {', '.join(flags)}", language=None)

    with st.expander(f"Generic branching ({len(generic_countries)} markets)", expanded=False):
        st.markdown("These markets use standard IF/ELSIF/ELSE language branching.")
        for c in generic_countries:
            rule = RULES[c]
            parts = []
            if "else_prefix" in rule:
                parts.append(f"else={rule['else_prefix']}")
            if "suppress_prefixes" in rule:
                parts.append(f"suppress={rule['suppress_prefixes']}")
            if "only_explicit_prefixes" in rule:
                parts.append(f"explicit={rule['only_explicit_prefixes']}")
            st.code(f"{c}: {', '.join(parts)}", language=None)

    st.divider()
    st.caption("Supported content types: Standard (Copy), Modal, Push (Copy_0-6), Numbered fields")

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.title("Liquid Template Generator")
st.markdown(
    "Upload a JSON content file to auto-detect its format "
    "(Standard, Modal, or Push) and generate Liquid template files "
    "with the correct market/language conditionals."
)

# ---------------------------------------------------------------------------
# Step 1: Upload
# ---------------------------------------------------------------------------

st.header("1. Upload JSON File")

uploaded_file = st.file_uploader(
    "Choose your JSON content file",
    type=["json"],
    help="The file should follow the expected structure: {\"a\": {\"modules\": [{\"content\": ...}]}}",
)

if uploaded_file is not None:
    # Parse JSON
    try:
        raw_text = uploaded_file.getvalue().decode("utf-8")
        data = json.loads(raw_text)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        st.error(f"Failed to parse JSON: {e}")
        st.stop()

    # Validate structure
    try:
        content = data["a"]["modules"][0]["content"]
    except (KeyError, IndexError, TypeError):
        st.error(
            "Unexpected JSON structure. Expected `data[\"a\"][\"modules\"][0][\"content\"]`."
        )
        st.stop()

    st.success(f"Loaded **{uploaded_file.name}** ({len(raw_text):,} bytes)")

    # Show detected content keys
    with st.expander("Detected content keys", expanded=False):
        st.json(list(content.keys()))

    # -------------------------------------------------------------------
    # Step 2: Generate
    # -------------------------------------------------------------------

    st.header("2. Generate Templates")

    if st.button("Generate Liquid Files", type="primary", use_container_width=True):
        with st.spinner("Processing..."):
            try:
                written, skipped = process_json(data)
            except Exception as e:
                st.error(f"Processing error: {e}")
                st.stop()

        # Store in session for download
        st.session_state["written"] = written
        st.session_state["skipped"] = skipped

    # -------------------------------------------------------------------
    # Step 3: Preview & Download
    # -------------------------------------------------------------------

    if "written" in st.session_state:
        written = st.session_state["written"]
        skipped = st.session_state["skipped"]

        st.header("3. Results")

        col1, col2 = st.columns(2)
        col1.metric("Files Generated", len(written))
        col2.metric("Skipped (no data)", len(skipped))

        if skipped:
            with st.expander("Skipped fields"):
                for s in skipped:
                    st.text(f"  - {s}")

        if written:
            # Preview each file
            st.subheader("Preview")
            tabs = st.tabs(list(written.keys()))
            for tab, (filename, liquid_content) in zip(tabs, written.items()):
                with tab:
                    st.code(liquid_content, language="liquid", line_numbers=True)

            # Download section
            st.subheader("Download")

            dl_col1, dl_col2 = st.columns(2)

            # Individual file downloads
            with dl_col1:
                st.markdown("**Individual files:**")
                for filename, liquid_content in written.items():
                    st.download_button(
                        label=f"Download {filename}",
                        data=liquid_content,
                        file_name=filename,
                        mime="text/plain",
                        key=f"dl_{filename}",
                    )

            # ZIP download
            with dl_col2:
                st.markdown("**All files as ZIP:**")
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for filename, liquid_content in written.items():
                        zf.writestr(filename, liquid_content)
                zip_buffer.seek(0)

                zip_name = uploaded_file.name.rsplit(".", 1)[0] + "_liquid.zip"
                st.download_button(
                    label=f"Download all ({len(written)} files)",
                    data=zip_buffer,
                    file_name=zip_name,
                    mime="application/zip",
                    key="dl_zip",
                    type="primary",
                )

else:
    # Placeholder when no file is uploaded
    st.info("Upload a JSON file to get started.")
