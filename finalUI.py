import streamlit as st
import pandas as pd
import os
import json
import random
from datetime import datetime

# -------------------------
# Page Config & Style
# -------------------------
st.set_page_config(page_title="⚓ Mooring Line Tension Dashboard", layout="wide")

st.markdown("""
<style>
.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

st.title("⚓ Mooring Line Tension Dashboard")
st.caption("Monitoring live mooring line tension readings from JSON data files.")

# -------------------------
# Folder Path
# -------------------------
folder_path = r"C:\Users\THINKPAD\Downloads\json hackathon-20251113T041221Z-1-001"

if not os.path.exists(folder_path):
    st.error("❌ Folder not found!")
    st.stop()

json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
if not json_files:
    st.warning("⚠️ No JSON files found!")
    st.stop()

# Pick a random JSON file each refresh
selected_file = random.choice(json_files)
file_path = os.path.join(folder_path, selected_file)

# -------------------------
# Thresholds
# -------------------------
warning_threshold = st.sidebar.number_input("🟧 Warning Threshold (kN)", value=2)
critical_threshold = st.sidebar.number_input("🔴 Critical Threshold (kN)", value=4)

# -------------------------
# Load JSON & Extract Hooks
# -------------------------
with open(file_path, "r") as f:
    data = json.load(f)

rows = []
for berth in data.get("berths", []):
    ship_name = berth.get("ship", {}).get("name", "Unknown Ship")
    berth_name = berth.get("name", "Unknown Berth")
    for bollard in berth.get("bollards", []):
        for hook in bollard.get("hooks", []):
            tension = hook.get("tension") or 0

            # Determine Status
            if tension >= critical_threshold:
                status = "CRITICAL"
                color = "#e74c3c"
                action = "🚨 Immediate action!"
            elif tension >= warning_threshold:
                status = "WARNING"
                color = "#f39c12"
                action = "⚠️ Slight loosen"
            else:
                status = "NORMAL"
                color = "#2ecc71"
                action = "✅ None"

            overload_percent = ((tension - warning_threshold) / warning_threshold * 100) if tension >= warning_threshold else 0

            rows.append({
                "Ship": ship_name,
                "Berth": berth_name,
                "Hook": hook.get("name"),
                "Tension (kN)": tension,
                "Status": status,
                "Overload (%)": round(overload_percent, 1),
                "Action": action,
                "Color": color
            })

df = pd.DataFrame(rows)

# -------------------------
# Ship Selector
# -------------------------
ships = sorted(df["Ship"].unique())
selected_ship = st.selectbox("🚢 Select Ship", ships)
df_ship = df[df["Ship"] == selected_ship]

# -------------------------
# Metrics Summary
# -------------------------
total_hooks = len(df_ship)
critical_hooks = (df_ship["Status"] == "CRITICAL").sum()
warning_hooks = (df_ship["Status"] == "WARNING").sum()
normal_hooks = (df_ship["Status"] == "NORMAL").sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("📊 Total Hooks", total_hooks)
col2.metric("🔴 Critical", critical_hooks)
col3.metric("🟧 Warning", warning_hooks)
col4.metric("🟢 Normal", normal_hooks)

# Alert box
if critical_hooks > 0:
    st.error(f"🚨 {critical_hooks} hooks require **immediate attention!**")
elif warning_hooks > 0:
    st.warning(f"⚠️ {warning_hooks} hooks are approaching overload threshold.")
else:
    st.success("✅ All hooks operating within normal tension range.")

# -------------------------
# Styled Hook Table
# -------------------------
df_display = df_ship.drop(columns=["Color"])
df_styled = df_display.style.apply(
    lambda x: [
        f"background-color: {df_ship.loc[x.name, 'Color']}; color: white; font-weight:bold"
        if v == df_ship.loc[x.name, "Status"] else ""
        for v in x
    ],
    axis=1
)

st.markdown("---")
st.markdown(f"### 🕒 Last Update: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`")
st.markdown(f"📄 Current JSON: `{selected_file}`")
st.dataframe(df_styled, use_container_width=True, height=500)

st.markdown("---")
st.caption("⚓ Mooring Line Tension System v2.0 | Manual refresh required. Each refresh shows a random JSON file.")
