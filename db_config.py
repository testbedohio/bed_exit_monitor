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
DB_HOST     = "db.qsnsxhpppqrbmlmjanyu.supabase.co"
DB_NAME     = "postgres"
DB_PORT     = 5432
DB_USER     = "postgres"
DB_PASSWORD = "23kawff-Jaxzo52435quzv.94yhslccs4r"

# --- Supabase REST API ---
# Found in: Supabase Dashboard -> Settings -> API
SUPABASE_URL      = "https://qsnsxhpppqrbmlmjanyu.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_MSmQi-seiMe4CiUYAfMOnA_Ogv_64kN"

# --- n8n Google Sheet Webhook ---
# Paste the Production webhook URL here after creating the n8n workflow.
# This webhook receives each alert log entry and appends it to Google Sheets.
N8N_SHEET_WEBHOOK = "https://testbed999.app.n8n.cloud/webhook/YOUR_SHEET_WEBHOOK_ID"
