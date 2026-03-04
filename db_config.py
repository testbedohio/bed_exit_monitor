# db_config.py
# ---------------------------------------------------------------------------
# SENSITIVE CREDENTIALS - DO NOT COMMIT THIS FILE TO GITHUB.
# This file is listed in .gitignore to prevent accidental exposure.
#
# HOW TO USE:
#   1. Fill in each value below with your real credentials.
#   2. Save this file in your bed_exit_monitor project folder.
#   3. The app will import it automatically.
#   4. Never share this file or paste its contents into chat/email.
#   5. When deploying to a new machine, copy this file manually.
# ---------------------------------------------------------------------------

# --- Supabase / PostgreSQL Connection ---
# Found in: Supabase Dashboard -> Settings -> Database -> Connection parameters
DB_HOST     = "db.qsnsxhpppqrbmlmjanyu.supabase.co"
DB_NAME     = "postgres"
DB_PORT     = 5432
DB_USER     = "postgres"
DB_PASSWORD = "YOUR_NEW_ROTATED_PASSWORD"   # <-- fill in your new password here

# --- Supabase REST API ---
# Found in: Supabase Dashboard -> Settings -> API
SUPABASE_URL      = "https://qsnsxhpppqrbmlmjanyu.supabase.co"
SUPABASE_ANON_KEY = "YOUR_NEW_ANON_KEY"     # <-- fill in your new anon key here

# --- n8n Google Sheet Webhook ---
# Paste the Production webhook URL here after creating the n8n workflow.
N8N_SHEET_WEBHOOK = "https://testbed999.app.n8n.cloud/webhook/YOUR_SHEET_WEBHOOK_ID"
