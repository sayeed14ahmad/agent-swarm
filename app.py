import streamlit as st
import subprocess
import os

st.set_page_config(page_title="FinSwarm Boardroom", layout="wide")

st.title("🏛️ FinNova Capital Boardroom Swarm")
st.markdown("**Theme A: FinSwarm** — Deterministic Multi-Agent Corporate Decision Engine")

# Sidebar configuration
st.sidebar.header("Simulation Controls")
case_choice = st.sidebar.radio("Select Scenario:", ["Baseline Case", "Surprise Case"])

if st.sidebar.button("🚀 Run Boardroom Simulation", type="primary"):
    with st.spinner("Agents are analyzing, challenging, and debating..."):
        mode = "baseline" if case_choice == "Baseline Case" else "surprise"
        
        # Explicitly pass current environment variables (including API keys) to the subprocess
        current_env = os.environ.copy()
        result = subprocess.run(
            ["python", "boardroom_swarm.py", mode], 
            capture_output=True, 
            text=True,
            env=current_env
        )
        
        if result.returncode == 0:
            st.success("Boardroom session finalized successfully!")
        else:
            st.error(f"Execution notice: {result.stderr}")

st.divider()

# Display Trace Output
case_filename = "Baseline_Trace.txt" if case_choice == "Baseline Case" else "Surprise_Trace.txt"
st.subheader(f"📊 Live Execution Trace: {case_filename}")

if os.path.exists(case_filename):
    with open(case_filename, "r", encoding="utf-8") as f:
        trace_data = f.read()
    st.text_area("Agent Debate Log & Final Decision", trace_data, height=500)
else:
    st.info("Click 'Run Boardroom Simulation' in the sidebar to generate the trace output.")