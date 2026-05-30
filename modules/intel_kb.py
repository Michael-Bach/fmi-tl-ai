"""
Persistent Intelligence Knowledge Base.

Backs the Intelligence tab with SQLite so product assessments survive
page refreshes and accumulate over time. Supports search, filtering,
bulk comparison, CSV export, and deletion.
"""
import json
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

_DB_PATH = Path(__file__).parent.parent / "data" / "intel_kb.db"

_DDL = """
CREATE TABLE IF NOT EXISTS products (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    label                TEXT    NOT NULL,
    date_added           TEXT    NOT NULL,
    source_type          TEXT,
    source               TEXT,
    core_capability      TEXT,
    recommendation       TEXT,
    itar_flag            INTEGER DEFAULT 0,
    dual_use_flag        INTEGER DEFAULT 0,
    classification_flag  INTEGER DEFAULT 0,
    relevance            TEXT,
    fit                  TEXT,
    acquisition_pathway  TEXT,
    next_step            TEXT,
    risk_summary         TEXT,
    flagged_claims_json  TEXT
);
"""

_REC_COLOR = {"evaluate": "🟢", "monitor": "🟡", "reject": "🔴"}


def _conn():
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(_DB_PATH)
    con.execute(_DDL)
    con.commit()
    return con


def _insert(con, row: dict):
    con.execute(
        """INSERT INTO products
           (label, date_added, source_type, source, core_capability,
            recommendation, itar_flag, dual_use_flag, classification_flag,
            relevance, fit, acquisition_pathway, next_step, risk_summary,
            flagged_claims_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            row["label"], row["date_added"], row.get("source_type", ""),
            row.get("source", ""), row.get("core_capability", ""),
            row.get("recommendation", "monitor"),
            int(row.get("itar_flag", False)), int(row.get("dual_use_flag", False)),
            int(row.get("classification_flag", False)),
            row.get("relevance", ""), row.get("fit", ""),
            row.get("acquisition_pathway", ""), row.get("next_step", ""),
            row.get("risk_summary", ""), json.dumps(row.get("flagged_claims", [])),
        ),
    )
    con.commit()


def _all_products(con) -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM products ORDER BY date_added DESC, id DESC", con)
    return df


def _delete(con, product_id: int):
    con.execute("DELETE FROM products WHERE id = ?", (product_id,))
    con.commit()


def _import_from_session(con):
    """Import products accumulated in the Intelligence tab session state."""
    products = st.session_state.get("products", [])
    if not products:
        return 0
    imported = 0
    for p in products:
        analysis   = p.get("analysis")
        assessment = p.get("assessment")
        if not analysis or not assessment:
            continue
        claims = []
        if hasattr(analysis, "flagged_claims"):
            for c in analysis.flagged_claims:
                claims.append({"claim": c.claim, "credibility": c.credibility})
        row = {
            "label":               p.get("name", analysis.product_name),
            "date_added":          str(date.today()),
            "source_type":         p.get("source_type", ""),
            "source":              "",
            "core_capability":     analysis.core_capability,
            "recommendation":      assessment.recommendation,
            "itar_flag":           assessment.itar_flag,
            "dual_use_flag":       assessment.dual_use_flag,
            "classification_flag": assessment.classification_concern,
            "relevance":           assessment.relevance,
            "fit":                 assessment.fit,
            "acquisition_pathway": assessment.acquisition_pathway,
            "next_step":           assessment.next_step,
            "risk_summary":        assessment.risk_summary,
            "flagged_claims":      claims,
        }
        _insert(con, row)
        imported += 1
    return imported


def _add_manual_form(con):
    st.subheader("Add product manually")
    with st.form("kb_manual_add"):
        label = st.text_input("Product label *")
        core  = st.text_area("Core capability", height=80)
        rec   = st.selectbox("Recommendation", ["evaluate", "monitor", "reject"])
        rel   = st.text_area("Relevance to Denmark", height=60)
        nxt   = st.text_input("Next step")
        c1, c2, c3 = st.columns(3)
        itar  = c1.checkbox("ITAR")
        dual  = c2.checkbox("Dual-use")
        cls   = c3.checkbox("Classification concern")
        src_t = st.selectbox("Source type", ["web page", "PDF document", "text snippet", "meeting", "other"])
        src   = st.text_input("Source URL / reference")
        submitted = st.form_submit_button("Add to Knowledge Base", type="primary")
        if submitted:
            if not label.strip():
                st.error("Label is required.")
            else:
                _insert(con, {
                    "label": label, "date_added": str(date.today()),
                    "source_type": src_t, "source": src,
                    "core_capability": core, "recommendation": rec,
                    "itar_flag": itar, "dual_use_flag": dual,
                    "classification_flag": cls,
                    "relevance": rel, "next_step": nxt,
                })
                st.success(f"Added: {label}")
                st.rerun()


def render():
    st.header("Intelligence Knowledge Base")
    st.caption(
        "Persistent, searchable store of product assessments. "
        "Import from the Intelligence tab, add manually, filter and compare. "
        "Survives page refreshes — data stored in SQLite."
    )

    con = _conn()

    # Top controls
    col_imp, col_clr, col_csv = st.columns([2, 1, 1])
    with col_imp:
        if st.button("⬇ Import from Intelligence tab", type="primary",
                      help="Imports all products currently in the Intelligence tab session."):
            n = _import_from_session(con)
            if n:
                st.success(f"Imported {n} product(s).")
                st.rerun()
            else:
                st.info("No products in Intelligence tab session to import. "
                        "Run an analysis there first.")
    with col_clr:
        if st.button("🗑 Clear entire KB",
                      help="Permanently deletes all knowledge base entries."):
            st.session_state["kb_confirm_clear"] = True
    if st.session_state.get("kb_confirm_clear"):
        st.warning("This will delete ALL KB entries. Are you sure?")
        c1, c2 = st.columns(2)
        if c1.button("Yes, clear", type="primary"):
            con.execute("DELETE FROM products")
            con.commit()
            st.session_state.pop("kb_confirm_clear", None)
            st.rerun()
        if c2.button("Cancel"):
            st.session_state.pop("kb_confirm_clear", None)
            st.rerun()

    df = _all_products(con)

    if df.empty:
        st.info("Knowledge base is empty. Import from the Intelligence tab or add a product manually below.")
        _add_manual_form(con)
        return

    # Filters
    with st.expander("🔍 Filter", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        rec_filter  = fc1.multiselect("Recommendation", ["evaluate", "monitor", "reject"],
                                       default=["evaluate", "monitor", "reject"])
        itar_filter = fc2.selectbox("ITAR flag", ["All", "Yes", "No"])
        search      = fc3.text_input("Search label / capability")

    mask = df["recommendation"].isin(rec_filter)
    if itar_filter == "Yes":  mask &= df["itar_flag"] == 1
    if itar_filter == "No":   mask &= df["itar_flag"] == 0
    if search.strip():
        mask &= (df["label"].str.contains(search, case=False, na=False) |
                 df["core_capability"].str.contains(search, case=False, na=False))
    fdf = df[mask]

    st.caption(f"{len(fdf)} of {len(df)} products shown.")

    # Comparison table
    display_cols = ["id", "date_added", "label", "recommendation",
                     "itar_flag", "dual_use_flag", "core_capability", "next_step"]
    show_df = fdf[display_cols].copy()
    show_df["recommendation"] = show_df["recommendation"].map(
        lambda r: f"{_REC_COLOR.get(r, '')} {r}"
    )
    show_df.rename(columns={"itar_flag": "ITAR", "dual_use_flag": "Dual-use",
                              "core_capability": "Capability"}, inplace=True)
    st.dataframe(show_df, use_container_width=True, hide_index=True)

    with col_csv:
        csv = fdf.to_csv(index=False)
        st.download_button("⬇ Export CSV", data=csv,
                            file_name=f"intel_kb_{date.today()}.csv",
                            mime="text/csv")

    # Detail expanders
    for _, row in fdf.iterrows():
        rec = row["recommendation"]
        with st.expander(f"{_REC_COLOR.get(rec, '')} {row['label']} — {row['date_added']}"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**Capability:** {row['core_capability']}")
                st.markdown(f"**Relevance:** {row['relevance']}")
                st.markdown(f"**Fit:** {row['fit']}")
                st.markdown(f"**Next step:** {row['next_step']}")
            with c2:
                flags = []
                if row["itar_flag"]:           flags.append("🇺🇸 ITAR")
                if row["dual_use_flag"]:        flags.append("🇪🇺 Dual-use")
                if row["classification_flag"]:  flags.append("🔒 Classification")
                st.markdown("**Flags:** " + ("  ".join(flags) if flags else "None"))
                if row["risk_summary"]:
                    st.caption(row["risk_summary"][:200])
            if st.button("Delete", key=f"del_{row['id']}"):
                _delete(con, int(row["id"]))
                st.rerun()

    st.divider()
    _add_manual_form(con)
