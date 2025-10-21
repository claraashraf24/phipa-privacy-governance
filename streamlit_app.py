import os
import time
import requests
import pandas as pd
import streamlit as st
from datetime import datetime
from io import BytesIO

# -------------------------------------------------------------------
# 🌐 API Configuration
# -------------------------------------------------------------------
API_BASE = os.getenv("API_BASE", "https://phipa-privacy-governance.onrender.com")

st.set_page_config(
    page_title="PHIPA Compliance Dashboard",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PHIPA-Compliant Privacy & Consent Governance")
st.caption("Live compliance telemetry for healthcare data access • demo system (synthetic data)")

# -------------------------------------------------------------------
# 🧭 Helper Functions
# -------------------------------------------------------------------
def fetch(path, params=None):
    """Wrapper for safe API requests."""
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=30)
        st.caption(f"→ Fetching {path} with {params}")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error on {path}: {e}")
        return None


def colored_metric(label, value, delta=None, threshold=None, suffix="%"):
    """Display KPI metric box with color-coded emoji."""
    color_emoji = "🟢"
    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        numeric_value = 0.0

    if threshold:
        if numeric_value < threshold[0]:
            color_emoji = "🔴"
        elif numeric_value < threshold[1]:
            color_emoji = "🟠"

    display_value = f"{numeric_value:.2f}{suffix}" if suffix else str(value)
    st.metric(f"{color_emoji} {label}", display_value, delta)


def convert_df_to_csv(df: pd.DataFrame):
    """Convert DataFrame to CSV bytes for download."""
    return df.to_csv(index=False).encode("utf-8")


def convert_df_to_excel(df: pd.DataFrame):
    """Convert DataFrame to Excel bytes for download."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="data")
    return buffer.getvalue()

# -------------------------------------------------------------------
# 🧩 Sidebar: Filters & Simulation Tools
# -------------------------------------------------------------------
st.sidebar.header("📋 Filters")

with st.sidebar.form("filters_form"):
    since_minutes = st.slider("Time Window (minutes)", 30, 24 * 60, 240, 30)
    limit_logs = st.slider("Max rows (logs)", 50, 2000, 500, 50)

    # Load users/patients for dropdowns
    users = fetch("/users/") or []
    patients = fetch("/patients/") or []

    user_map = {u["id"]: f'{u["name"]} ({u["role"]})' for u in users}
    patient_map = {p["id"]: f'{p["name"]} [#{p["id"]}]' for p in patients}

    sel_user = st.selectbox("User (optional)", [None] + list(user_map.keys()),
                            format_func=lambda k: "All users" if k is None else user_map[k])
    sel_patient = st.selectbox("Patient (optional)", [None] + list(patient_map.keys()),
                               format_func=lambda k: "All patients" if k is None else patient_map[k])
    sel_action = st.selectbox("Action", [None, "view", "edit", "export"],
                              format_func=lambda v: "All actions" if v is None else v)

    apply_filters = st.form_submit_button("✅ Apply Filters")

# Default first load
if "first_load" not in st.session_state:
    st.session_state.first_load = True
    apply_filters = True

# Simulation panel
st.sidebar.divider()
st.sidebar.subheader("🧪 Simulation Tools")

sel_user_sim = st.sidebar.selectbox("Select user", [None] + [u["id"] for u in users],
                                    format_func=lambda k: "Select a user" if k is None else user_map[k])
sel_patient_sim = st.sidebar.selectbox("Select patient", [None] + [p["id"] for p in patients],
                                       format_func=lambda k: "Select a patient" if k is None else patient_map[k])
sim_action = st.sidebar.selectbox("Simulated action", ["view", "edit", "export"], index=1)

if st.sidebar.button("🚨 Simulate Unauthorized Access"):
    if sel_user_sim and sel_patient_sim:
        payload = {"user_id": sel_user_sim, "patient_id": sel_patient_sim, "action": sim_action}
        resp = requests.post(f"{API_BASE}/access/", json=payload)
        if resp.status_code == 200:
            st.sidebar.success("✅ Access simulated successfully.")
        else:
            st.sidebar.error(f"❌ Simulation failed: {resp.text}")
    else:
        st.sidebar.warning("Please select both a user and a patient first.")

# -------------------------------------------------------------------
# 📊 Load Data with Persistent State
# -------------------------------------------------------------------
if "metrics" not in st.session_state:
    st.session_state.metrics = {}
if "logs" not in st.session_state:
    st.session_state.logs = []

# Fetch only when filters applied or first load
if apply_filters or st.session_state.first_load:
    with st.spinner("Fetching filtered data..."):
        st.session_state.metrics = fetch("/metrics/overview", params={"since_minutes": since_minutes}) or {}
        st.session_state.logs = fetch("/logs", params={"limit": limit_logs, "since_minutes": since_minutes}) or []
    st.session_state.first_load = False

metrics = st.session_state.metrics
logs = st.session_state.logs

# -------------------------------------------------------------------
# 🧮 KPI Metrics Section
# -------------------------------------------------------------------
st.subheader("📊 Compliance Summary")

if not metrics:
    st.warning("⚠️ No metrics available yet. Apply filters to load data.")
else:
    kpi_cols = st.columns(4)
    compliance_pct = metrics.get("compliance_pct", 100)
    accesses = metrics.get("total_accesses", 0)
    breaches = metrics.get("breaches", 0)
    open_alerts = metrics.get("open_alerts", 0)

    with kpi_cols[0]:
        colored_metric("Compliance (authorized %)", compliance_pct, threshold=(60, 85))
    with kpi_cols[1]:
        st.metric("Accesses (window)", accesses)
    with kpi_cols[2]:
        st.metric(("💣" if breaches > 0 else "🟢") + " Breaches (window)", breaches)
    with kpi_cols[3]:
        st.metric(("⚠️" if open_alerts > 0 else "✅") + " Open Alerts", open_alerts)

    st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    st.divider()

# -------------------------------------------------------------------
# 📈 Trend Chart
# -------------------------------------------------------------------
st.subheader("📈 Access Trends (Last Window)")
series = metrics.get("series", []) if metrics else []
if series:
    df_series = pd.DataFrame(series)
    df_series["bucket"] = pd.to_datetime(df_series["bucket"])
    df_series = df_series.set_index("bucket")
    st.line_chart(df_series[["authorized", "breaches"]])
else:
    st.info("No time-series data yet. Simulate some accesses to visualize trends.")

st.divider()

# -------------------------------------------------------------------
# 🧾 Access Logs
# -------------------------------------------------------------------
st.subheader("🧾 Access Logs")
if logs:
    df_logs = pd.json_normalize(logs)
    df_logs["user"] = df_logs["user_id"].map(user_map).fillna(df_logs["user_id"].astype(str))
    df_logs["patient"] = df_logs["patient_id"].map(patient_map).fillna(df_logs["patient_id"].astype(str))
    df_logs["when"] = pd.to_datetime(df_logs["timestamp"])
    df_logs = df_logs.sort_values("when", ascending=False)

    display_df = df_logs[["when", "user", "patient", "action", "is_authorized"]].rename(columns={
        "when": "Timestamp", "user": "User", "patient": "Patient",
        "action": "Action", "is_authorized": "Authorized"
    })

    st.dataframe(display_df, width='stretch', height=360)

    csv = convert_df_to_csv(display_df)
    excel = convert_df_to_excel(display_df)
    st.download_button("⬇️ Download Access Logs (CSV)", csv, "access_logs.csv", "text/csv")
    st.download_button("⬇️ Download Access Logs (Excel)", excel, "access_logs.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.info("No access logs found for the selected window or filters.")

st.divider()

# -------------------------------------------------------------------
# 🚨 Alerts
# -------------------------------------------------------------------
st.subheader("🚨 Active Alerts")
alerts = fetch("/alerts", params={"limit": 100, "unresolved_only": False}) or []
if alerts:
    df_alerts = pd.json_normalize(alerts)
    df_alerts["created_at"] = pd.to_datetime(df_alerts["created_at"])
    df_alerts = df_alerts.sort_values("created_at", ascending=False)
    st.dataframe(
        df_alerts[["created_at", "message", "resolved"]].rename(columns={
            "created_at": "Created At", "message": "Message", "resolved": "Resolved"
        }),
        width='stretch', height=260
    )
    csv = convert_df_to_csv(df_alerts)
    st.download_button("⬇️ Download Alerts (CSV)", csv, "alerts.csv", "text/csv")
else:
    st.success("No unresolved alerts 🎉")

st.divider()

# -------------------------------------------------------------------
# 🧠 Incident Summaries
# -------------------------------------------------------------------
st.subheader("🧠 Incident Summaries (Narrative)")
summ = fetch("/incidents/summaries")
if summ:
    df_sum = pd.json_normalize(summ)
    df_sum["created_at"] = pd.to_datetime(df_sum["created_at"])
    df_sum = df_sum.sort_values("created_at", ascending=False)
    for _, row in df_sum.iterrows():
        st.markdown(f"**{row['created_at']}** — {row['summary']}")
else:
    st.info("No incident summaries yet.")

st.divider()

# -------------------------------------------------------------------
# 🧩 Consent Matrix
# -------------------------------------------------------------------
with st.expander("🧾 Consent Matrix (who can view/edit whom)"):
    cm = fetch("/consent-matrix") or []
    if cm:
        df_cm = pd.DataFrame(cm)
        df_cm = df_cm[["user_name", "role", "patient_name", "can_view", "can_edit"]]
        df_cm = df_cm.rename(columns={
            "user_name": "User", "role": "Role", "patient_name": "Patient",
            "can_view": "Can View", "can_edit": "Can Edit"
        })
        st.dataframe(df_cm, width='stretch', height=280)
        csv = convert_df_to_csv(df_cm)
        st.download_button("⬇️ Download Consent Matrix (CSV)", csv, "consent_matrix.csv", "text/csv")
    else:
        st.info("No consents yet. Create some to populate the matrix.")

# -------------------------------------------------------------------
# 🔄 Manual Refresh + Timestamp
# -------------------------------------------------------------------
st.divider()
col1, col2 = st.columns([0.25, 0.75])
with col1:
    if st.button("🔄 Refresh Data"):
        st.session_state.metrics = fetch("/metrics/overview", params={"since_minutes": since_minutes}) or {}
        st.session_state.logs = fetch("/logs", params={"limit": limit_logs, "since_minutes": since_minutes}) or {}
        st.session_state.last_refresh = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        st.rerun()
with col2:
    last_refresh = st.session_state.get("last_refresh", None)
    if last_refresh:
        st.caption(f"Last refreshed at: {last_refresh}")
    else:
        st.caption("Data not refreshed yet — click the button above to reload.")

# -------------------------------------------------------------------
# ℹ️ About / Disclaimer
# -------------------------------------------------------------------
with st.expander("ℹ️ About This Demo"):
    st.markdown("""
    **PHIPA Compliance Governance Dashboard (Demo)**  
    This is a *simulated environment* for illustrating healthcare privacy telemetry and access-governance workflows.  
    It is **not an official PHIPA-certified system** and should not be used with real patient data.

    **Purpose:**  
    - Demonstrate how live data access can be logged, analyzed, and visualized.  
    - Educate healthcare developers and compliance teams on privacy-by-design concepts.  
    - Serve as a base for integrating actual PHIPA/HIPAA compliance modules in production.
    """)

# -------------------------------------------------------------------
# 🧾 Footer
# -------------------------------------------------------------------
st.markdown("""
---
**© 2025 PHIPA Compliance Simulation | Built with FastAPI + Streamlit**
""")
