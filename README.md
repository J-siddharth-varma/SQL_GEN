# ⚡ SQL Generator

> Turn plain English into precise SQL — powered by Google Gemini AI.

## Features

- 🧠 **Natural Language → SQL** — Describe what you want in English, get a ready-to-run SQL query.
- 📂 **Dual Schema Input** — Paste `CREATE TABLE` statements _or_ upload a `.db` file.
- ▶️ **Live Execution** — Run generated queries against your uploaded SQLite database and see results instantly.
- ✏️ **Editable Output** — Tweak the generated SQL before executing.
- 📜 **Query History** — Keeps your last 20 queries in the session.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Generate a sample database for testing
python create_sample_db.py

# 3. Run the app
streamlit run app.py
```

## API Key Configuration

1. Get a free API key at [Google AI Studio](https://aistudio.google.com/apikey).
2. You can provide your key in either of two ways:
   - **In the UI**: Enter it into the password field in the sidebar (hidden from view).
   - **As an Environment Variable**: Set `GEMINI_API_KEY=your_key` or add it to `.streamlit/secrets.toml` as `GEMINI_API_KEY = "your_key"`.

> Note: Never commit your API key or `.env` files to source control. A `.gitignore` is included by default.

## Project Structure

```
SQL_GEN/
├── .streamlit/
│   └── config.toml        # Custom dark theme
├── .env.example            # Example environment file
├── .gitignore             # Ignored secrets, databases, caches
├── app.py                  # Main Streamlit application
├── create_sample_db.py     # Script to generate a test SQLite DB
├── requirements.txt        # Python dependencies
└── README.md
```
