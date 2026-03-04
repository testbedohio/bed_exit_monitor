# secrets.py
# ---------------------------------------------------------------------------
# SENSITIVE CREDENTIALS - DO NOT COMMIT THIS FILE TO GITHUB.
# This file is listed in .gitignore to prevent accidental exposure.
#
# HOW TO USE:
#   1. Fill in each value below with your real credentials.
#   2. Save the file into your bed_exit_monitor project folder.
#   3. The app will import it automatically.
#   4. Never share this file or paste its contents into chat/email.
# ---------------------------------------------------------------------------

# --- Supabase / PostgreSQL Connection ---
# Found in: Supabase Dashboard -> Settings -> Database -> Connection parameters
DB_HOST     = "YOUR_SUPABASE_HOST"       # e.g. db.xxxxxxxxxxxx.supabase.co
DB_NAME     = "postgres"                 # usually 'postgres'
DB_PORT     = 5432                       # usually 5432
DB_USER     = "postgres"                 # usually 'postgres'
DB_PASSWORD = "YOUR_DATABASE_PASSWORD"  # the password you set when creating the project

# --- Supabase REST API ---
# Found in: Supabase Dashboard -> Settings -> API
SUPABASE_URL      = "https://xxxxxxxxxxxx.supabase.co"  # your project URL
SUPABASE_ANON_KEY = "YOUR_ANON_PUBLIC_KEY"              # the long 'anon' key

# --- n8n Google Sheet Webhook ---
# Paste the Production webhook URL here after creating the n8n workflow.
# This webhook receives each alert log entry and appends it to Google Sheets.
N8N_SHEET_WEBHOOK = "https://testbed999.app.n8n.cloud/webhook/YOUR_SHEET_WEBHOOK_ID"
