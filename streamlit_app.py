import os
import time
import requests
import pandas as pd
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="PHIPA Compliance Dashboard",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PHIPA-Compliant Privacy & Consent Governance")
st.caption("Live compliance telemetry for healthcare data access • demo system (synthetic data)")

# -------------------------------------------------------------------
# 🧭 Helper: API Fetch Wrapper
# -------------------------------------------------------------------
def fetch(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=10)
        st.caption(f"→ Fetching {path} with {params}")  # for visibility
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error on {path}: {e}")
        return None


# -------------------------------------------------------------------
# 🧩 Sidebar Filter Form
# -------------------------------------------------------------------
st.sidebar.header("Filters")

# Sidebar form (manual apply button)
with st.sidebar.form("filters_form"):
    since_minutes = st.slider("Time Window (minutes)", min_value=30, max_value=24*60, value=240, step=30)
    limit_logs = st.slider("Max rows (logs)", min_value=50, max_value=2000, value=500, step=50)
    auto_refresh = st.checkbox("Auto refresh (10s)", value=True)

    # Get users/patients for dropdowns
    users = fetch("/users/") or []
    patients = fetch("/patients/") or []

    user_map = {u["id"]: f'{u["name"]} ({u["role"]})' for u in users}
    patient_map = {p["id"]: f'{p["name"]} [#{p["id"]}]' for p in patients}

    sel_user = st.selectbox("User (optional)", options=[None] + list(user_map.keys()),
                            format_func=lambda k: "All users" if k is None else user_map[k])
    sel_patient = st.selectbox("Patient (optional)", options=[None] + list(patient_map.keys()),
                               format_func=lambda k: "All patients" if k is None else patient_map[k])
    sel_action = st.selectbox("Action", options=[None, "view", "edit", "export"],
                              format_func=lambda v: "All actions" if v is None else v)

    apply_filters = st.form_submit_button("✅ Apply Filters")

# -------------------------------------------------------------------
# 📊 KPI Metrics
# -------------------------------------------------------------------
metrics = fetch("/metrics/overview", params={"since_minutes": since_minutes}) or {}
kpi_cols = st.columns(4)
kpi_cols[0].metric("Compliance (authorized %)", f'{metrics.get("compliance_pct", 100):.2f}%')
kpi_cols[1].metric("Accesses (window)", metrics.get("total_accesses", 0))
kpi_cols[2].metric("Breaches (window)", metrics.get("breaches", 0))
kpi_cols[3].metric("Open Alerts", metrics.get("open_alerts", 0))
st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")

# -------------------------------------------------------------------
# 📁 Export / Download Buttons
# -------------------------------------------------------------------
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    if st.button("📄 Generate PHIPA Audit Report (PDF)"):
        pdf = requests.get(f"{API_BASE}/reports/audit", timeout=20)
        if pdf.ok:
            st.download_button(
                "⬇️ Download Report",
                data=pdf.content,
                file_name="PHIPA_Audit_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error("Failed to generate report.")

with c2:
    pats = requests.get(f"{API_BASE}/export/anonymized/patients", timeout=20)
    if pats.ok:
        st.download_button(
            "🔒 Download Anonymized Patients (CSV)",
            data=pats.content,
            file_name="anonymized_patients.csv",
            mime="text/csv",
            use_container_width=True
        )

with c3:
    logs_csv = requests.get(f"{API_BASE}/export/anonymized/logs", timeout=20, params={"since_minutes": since_minutes})
    if logs_csv.ok:
        st.download_button(
            "🔒 Download Anonymized Access Logs (CSV)",
            data=logs_csv.content,
            file_name="anonymized_access_logs.csv",
            mime="text/csv",
            use_container_width=True
        )

# -------------------------------------------------------------------
# 📈 Trend Chart
# -------------------------------------------------------------------
series = metrics.get("series", [])
if series:
    df_series = pd.DataFrame(series)
    df_series["bucket"] = pd.to_datetime(df_series["bucket"])
    df_series = df_series.set_index("bucket")
    st.line_chart(df_series[["authorized", "breaches"]])
else:
    st.info("No time-series data yet. Generate a few accesses to see the trend.")

st.divider()

# -------------------------------------------------------------------
# 🧾 Access Logs
# -------------------------------------------------------------------
params = {"limit": limit_logs, "since_minutes": since_minutes}
if sel_user is not None:
    params["user_id"] = sel_user
if sel_patient is not None:
    params["patient_id"] = sel_patient
if sel_action is not None:
    params["action"] = sel_action

if apply_filters:  # ✅ Only runs when Apply clicked
    logs = fetch("/logs", params=params) or []
    if logs:
        df_logs = pd.json_normalize(logs)
        df_logs["user"] = df_logs["user_id"].map(user_map).fillna(df_logs["user_id"].astype(str))
        df_logs["patient"] = df_logs["patient_id"].map(patient_map).fillna(df_logs["patient_id"].astype(str))
        df_logs["when"] = pd.to_datetime(df_logs["timestamp"])
        df_logs = df_logs.sort_values("when", ascending=False)

        st.subheader("Recent Access Events")
        st.dataframe(
            df_logs[["when", "user", "patient", "action", "is_authorized"]].rename(columns={
                "when": "Timestamp", "user": "User", "patient": "Patient",
                "action": "Action", "is_authorized": "Authorized"
            }),
            use_container_width=True, height=360
        )
    else:
        st.info("No access logs found for the selected window/filters.")

# -------------------------------------------------------------------
# 🚨 Alerts
# -------------------------------------------------------------------
st.subheader("Alerts")
alerts = fetch("/alerts", params={"limit": 100, "unresolved_only": False}) or []
if alerts:
    df_alerts = pd.json_normalize(alerts)
    df_alerts["created_at"] = pd.to_datetime(df_alerts["created_at"])
    df_alerts = df_alerts.sort_values("created_at", ascending=False)
    st.dataframe(
        df_alerts[["created_at", "message", "resolved"]].rename(columns={
            "created_at": "Created At", "message": "Message", "resolved": "Resolved"
        }),
        use_container_width=True, height=260
    )
else:
    st.success("No alerts 🎉")

# -------------------------------------------------------------------
# 🧠 Human-Readable Summaries
# -------------------------------------------------------------------
st.subheader("Incident Summaries (Human-Readable)")
summ = fetch("/incidents/summaries")
if summ:
    df_sum = pd.json_normalize(summ)
    df_sum["created_at"] = pd.to_datetime(df_sum["created_at"])
    df_sum = df_sum.sort_values("created_at", ascending=False)
    for _, row in df_sum.iterrows():
        st.markdown(f"**{row['created_at']}** — {row['summary']}")
else:
    st.info("No incident summaries yet.")

# -------------------------------------------------------------------
# 🧩 Consent Matrix
# -------------------------------------------------------------------
with st.expander("Consent Matrix (who can view/edit whom)"):
    cm = fetch("/consent-matrix") or []
    if cm:
        df_cm = pd.DataFrame(cm)
        df_cm = df_cm[["user_name", "role", "patient_name", "can_view", "can_edit"]]
        df_cm = df_cm.rename(columns={
            "user_name": "User", "role": "Role", "patient_name": "Patient",
            "can_view": "Can View", "can_edit": "Can Edit"
        })
        st.dataframe(df_cm, use_container_width=True, height=280)
    else:
        st.info("No consents yet. Create a few to populate the matrix.")

# -------------------------------------------------------------------
# 🔁 Auto Refresh
# -------------------------------------------------------------------
if auto_refresh:
    st.caption("Auto-refreshing every 10 seconds…")
    time.sleep(10)
    st.rerun()
