"""
SQL Generator — Convert natural language to SQL using Google Gemini.
Supports pasting a schema or uploading a SQLite .db file.
Generated queries can be executed live against the uploaded database.
"""

import sqlite3
import tempfile
import os
import textwrap
from pathlib import Path

import streamlit as st
from google import genai


# ──────────────────────────────────────────────
# Constants & helpers
# ──────────────────────────────────────────────

GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = textwrap.dedent("""\
    You are an expert SQL analyst. The user will give you a database schema and a
    natural-language question. Your job is to return **only** the SQL query that
    answers the question — no explanation, no markdown fences, no commentary.

    Rules:
    • Use standard SQL compatible with SQLite.
    • Never use SELECT *; always list columns explicitly.
    • If the question is ambiguous, make a reasonable assumption and proceed.
    • Return exactly one SQL statement, ending with a semicolon.
""")


def extract_schema_from_db(db_path: str) -> str:
    """Read every CREATE TABLE / CREATE VIEW statement from a SQLite file."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
    )
    statements = [row[0] for row in cursor.fetchall()]
    conn.close()
    return "\n\n".join(statements)


def get_table_names(db_path: str) -> list[str]:
    """Return a list of user table names."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return names


def preview_table(db_path: str, table: str, limit: int = 5) -> list[dict]:
    """Return the first `limit` rows from a table as a list of dicts."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(f'SELECT * FROM "{table}" LIMIT {limit}').fetchall()
    conn.close()
    return [dict(r) for r in rows]


@st.cache_resource
def _get_client(api_key: str) -> genai.Client:
    """Create and cache the Gemini client so it's reused across reruns."""
    return genai.Client(api_key=api_key)


def generate_sql(api_key: str, schema: str, question: str, model: str = GEMINI_MODEL) -> str:
    """Call Gemini to convert a natural-language question into SQL with minimal latency."""
    client = _get_client(api_key)

    prompt = f"### Schema\n{schema}\n\n### Question\n{question}"

    config_args = {
        "system_instruction": SYSTEM_PROMPT,
        "max_output_tokens": 512,       # SQL queries are concise
        "temperature": 0.0,              # Deterministic output
    }

    # Attempt to disable thinking budget (turns off 10-25s reasoning overhead)
    try:
        from google.genai import types
        config_args["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        config = genai.types.GenerateContentConfig(**config_args)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
    except Exception:
        # Fallback if model doesn't support thinking_config
        config_args.pop("thinking_config", None)
        config = genai.types.GenerateContentConfig(**config_args)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )

    sql = response.text.strip()

    # Strip markdown fences if the model wraps them anyway
    if sql.startswith("```"):
        lines = sql.splitlines()
        sql = "\n".join(lines[1:-1]).strip()

    return sql


def execute_sql(db_path: str, sql: str) -> tuple[list[str], list[tuple]]:
    """Execute SQL against a SQLite database and return (columns, rows)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(sql)
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    rows = cursor.fetchall()
    conn.close()
    return columns, rows


# ──────────────────────────────────────────────
# Custom CSS for a premium look
# ──────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
    /* ─── Import Google Font ─── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ─── Global ─── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ─── Hero header ─── */
    .hero {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
    }
    .hero h1 {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #7C3AED 0%, #EC4899 50%, #F59E0B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .hero p {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-top: 0;
    }

    /* ─── Glass cards ─── */
    .glass-card {
        background: rgba(30, 30, 60, 0.55);
        border: 1px solid rgba(124, 58, 237, 0.25);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(12px);
        margin-bottom: 1rem;
    }

    /* ─── Schema badge ─── */
    .schema-badge {
        display: inline-block;
        background: linear-gradient(135deg, #7C3AED, #6D28D9);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 0.2rem;
    }

    /* ─── Status pill ─── */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.85rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .status-pill.ok   { background: #064E3B; color: #6EE7B7; }
    .status-pill.warn { background: #78350F; color: #FCD34D; }

    /* ─── Divider ─── */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(124,58,237,0.4), transparent);
        margin: 1.5rem 0;
    }

    /* ─── Footer ─── */
    .footer {
        text-align: center;
        color: #475569;
        font-size: 0.8rem;
        padding: 2rem 0 1rem;
    }

    /* ─── Sidebar styling ─── */
    section[data-testid="stSidebar"] {
        background: #12122A;
    }
    </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Session-state initialisation
# ──────────────────────────────────────────────

def init_state():
    defaults = {
        "schema_text": "",
        "db_path": None,
        "generated_sql": "",
        "result_columns": [],
        "result_rows": [],
        "history": [],      # list of (question, sql) tuples
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ──────────────────────────────────────────────
# Sidebar — API key & schema input
# ──────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")

        # API key (check env var, .env file, or streamlit secrets as default)
        default_api_key = os.environ.get("GEMINI_API_KEY", "")
        if not default_api_key and os.path.exists(".env"):
            try:
                with open(".env", "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY="):
                            default_api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass
        if not default_api_key:
            try:
                default_api_key = st.secrets.get("GEMINI_API_KEY", "")
            except Exception:
                default_api_key = ""

        api_key = st.text_input(
            "Google Gemini API Key",
            value=default_api_key,
            type="password",
            help="Default key is pre-loaded if configured. You can edit, delete, or replace it with your own key anytime.",
        )
        if default_api_key:
            st.caption("🔒 Default key loaded. Feel free to edit or replace it.")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("### ⚡ AI Model")
        model_options = {
            "⚡ Gemini 2.5 Flash (Latest Free Tier - Recommended)": "gemini-2.5-flash",
            "🚀 Gemini 2.5 Flash-Lite (Ultra Fast)": "gemini-2.5-flash-lite",
            "🔄 Gemini 1.5 Flash (Fallback)": "gemini-1.5-flash",
        }
        selected_model_label = st.selectbox(
            "Model",
            options=list(model_options.keys()),
            index=0,
            help="Gemini 2.5 Flash is the latest free-tier model with reasoning overhead disabled for instant SQL output.",
        )
        selected_model = model_options[selected_model_label]

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("### 📂 Database Schema")

        schema_mode = st.radio(
            "How to provide your schema",
            ["✍️ Paste SQL", "📤 Upload .db file"],
            horizontal=True,
        )

        if schema_mode == "✍️ Paste SQL":
            schema_input = st.text_area(
                "Paste your CREATE TABLE statements",
                height=220,
                placeholder=(
                    "CREATE TABLE employees (\n"
                    "  id INTEGER PRIMARY KEY,\n"
                    "  name TEXT NOT NULL,\n"
                    "  department TEXT,\n"
                    "  salary REAL\n"
                )
            )
            if schema_input:
                st.session_state.schema_text = schema_input

        else:  # Upload .db
            uploaded = st.file_uploader("Upload a SQLite database", type=["db", "sqlite", "sqlite3"])
            if uploaded:
                # Only write the file once — skip if we already saved it
                if st.session_state.db_path is None or not os.path.exists(st.session_state.db_path):
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
                    tmp.write(uploaded.read())
                    tmp.close()
                    st.session_state.db_path = tmp.name
                    extracted = extract_schema_from_db(tmp.name)
                    st.session_state.schema_text = extracted
                st.success("Schema extracted ✔")

        # Show detected tables
        if st.session_state.schema_text:
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown("**Detected tables**")
            # Crude but fast — pull table names from CREATE TABLE lines
            tables = []
            for line in st.session_state.schema_text.splitlines():
                upper = line.strip().upper()
                if upper.startswith("CREATE TABLE"):
                    name = line.strip().split()[2].strip("(\"` ")
                    tables.append(name)
            badges = " ".join(f'<span class="schema-badge">{t}</span>' for t in tables)
            st.markdown(badges, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<p style="color:#64748B;font-size:0.78rem;">'
            'Powered by Google Gemini · Built with Streamlit'
            '</p>',
            unsafe_allow_html=True,
        )

    return api_key, selected_model


# ──────────────────────────────────────────────
# Main content area
# ──────────────────────────────────────────────

def render_main(api_key: str, model: str = GEMINI_MODEL):
    # Hero
    st.markdown(
        '<div class="hero">'
        '<h1>⚡ SQL Generator</h1>'
        '<p>Turn plain English into precise SQL — powered by AI</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Status bar
    schema_ok = bool(st.session_state.schema_text)
    key_ok = bool(api_key)

    col1, col2 = st.columns(2)
    with col1:
        if schema_ok:
            st.markdown('<span class="status-pill ok">✅ Schema loaded</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-pill warn">⚠️ No schema</span>', unsafe_allow_html=True)
    with col2:
        if key_ok:
            st.markdown('<span class="status-pill ok">🔑 API key set</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-pill warn">⚠️ No API key</span>', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Data preview (if .db uploaded) ──
    if st.session_state.db_path:
        with st.expander("🗄️ Preview database tables", expanded=False):
            tables = get_table_names(st.session_state.db_path)
            if tables:
                selected = st.selectbox("Table", tables)
                rows = preview_table(st.session_state.db_path, selected)
                if rows:
                    st.dataframe(rows, use_container_width=True)
                else:
                    st.info("Table is empty.")

    # ── Query input ──
    st.markdown("### 💬 Ask your question")
    question = st.text_input(
        "Natural language query",
        placeholder="e.g. Show me the top 5 employees by salary in the Engineering department",
        label_visibility="collapsed",
    )

    generate_btn = st.button("🚀  Generate SQL", type="primary", use_container_width=True)

    if generate_btn:
        if not key_ok:
            st.error("Please enter your Gemini API key in the sidebar.")
            return
        if not schema_ok:
            st.error("Please provide a database schema first.")
            return
        if not question.strip():
            st.warning("Type a question above before generating.")
            return

        with st.spinner("Generating SQL …"):
            try:
                sql = generate_sql(api_key, st.session_state.schema_text, question, model=model)
                st.session_state.generated_sql = sql
                st.session_state.result_columns = []
                st.session_state.result_rows = []
                # Save to history
                st.session_state.history.insert(0, (question, sql))
                if len(st.session_state.history) > 20:
                    st.session_state.history = st.session_state.history[:20]
            except Exception as exc:
                st.error(f"Gemini API error: {exc}")
                return

    # ── Display generated SQL ──
    if st.session_state.generated_sql:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("### 🧾 Generated SQL")
        st.code(st.session_state.generated_sql, language="sql")

        # Copy button
        st.markdown(
            f"""
            <textarea id="sql-copy" style="position:absolute;left:-9999px">{st.session_state.generated_sql}</textarea>
            """,
            unsafe_allow_html=True,
        )

        # Editable area so users can tweak before running
        edited_sql = st.text_area(
            "✏️ Edit SQL before executing (optional)",
            value=st.session_state.generated_sql,
            height=140,
        )

        # Execute button
        if st.session_state.db_path:
            run_btn = st.button("▶️  Execute Query", use_container_width=True)
            if run_btn:
                with st.spinner("Running query …"):
                    try:
                        cols, rows = execute_sql(st.session_state.db_path, edited_sql)
                        st.session_state.result_columns = cols
                        st.session_state.result_rows = rows
                    except Exception as exc:
                        st.error(f"SQL execution error: {exc}")
        else:
            st.info("💡 Upload a `.db` file in the sidebar to execute queries against it.")

    # ── Results table ──
    if st.session_state.result_columns:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("### 📊 Query Results")
        import pandas as pd
        df = pd.DataFrame(st.session_state.result_rows, columns=st.session_state.result_columns)
        st.dataframe(df, use_container_width=True, height=400)
        st.caption(f"{len(df)} row(s) returned")

    # ── History ──
    if st.session_state.history:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        with st.expander("📜 Query History", expanded=False):
            for i, (q, s) in enumerate(st.session_state.history):
                st.markdown(f"**{i+1}.** {q}")
                st.code(s, language="sql")

    # Footer
    st.markdown(
        '<div class="footer">SQL Generator · Gemini AI · © 2026</div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="SQL Generator — AI-Powered",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()
    init_state()
    api_key, model = render_sidebar()
    render_main(api_key, model=model)


if __name__ == "__main__":
    main()
