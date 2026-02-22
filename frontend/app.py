"""
FractalAuth — Streamlit Frontend  (app.py)
Run:  streamlit run app.py
"""

import streamlit as st
# ── Session State Initialization ─────────────────────────

if "mode" not in st.session_state:
    st.session_state.mode = "register"

if "step" not in st.session_state:
    st.session_state.step = 1

if "fractal_markers" not in st.session_state:
    st.session_state.fractal_markers = []

if "behavior_data" not in st.session_state:
    st.session_state.behavior_data = {}

if "fractal_type" not in st.session_state:
    st.session_state.fractal_type = "mandelbrot"

if "username" not in st.session_state:
    st.session_state.username = ""
st.set_page_config(
    page_title="FractalAuth",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600&display=swap');
html,body,[class*="css"]{font-family:'Rajdhani',sans-serif!important;background:#020408!important;color:#c8e6ff!important;}
.stApp{background:#020408;}
#MainMenu,footer,header{visibility:hidden;}
.stTextInput>div>div>input,.stPasswordInput>div>div>input{
  background:rgba(0,212,255,0.04)!important;border:1px solid #0a2040!important;
  border-radius:2px!important;color:#c8e6ff!important;font-family:'Share Tech Mono',monospace!important;}
.stTextInput>div>div>input:focus,.stPasswordInput>div>div>input:focus{
  border-color:#00d4ff!important;box-shadow:0 0 10px rgba(0,212,255,0.2)!important;}
.stButton>button{
  background:rgba(0,212,255,0.08)!important;color:#00d4ff!important;
  border:1px solid #00d4ff!important;border-radius:2px!important;
  font-family:'Orbitron',monospace!important;font-size:0.7rem!important;
  letter-spacing:2px!important;font-weight:700!important;}
.stButton>button:hover{background:rgba(0,212,255,0.18)!important;box-shadow:0 0 15px rgba(0,212,255,0.3)!important;}
[data-testid="stRadio"]>div{flex-direction:row;gap:20px;}
[data-testid="stRadio"] label{color:#c8e6ff!important;}
.stProgress>div>div>div{background:linear-gradient(90deg,#00d4ff,#00ff88)!important;}
[data-testid="metric-container"]{background:#060d16!important;border:1px solid #0a2040!important;padding:15px!important;border-radius:2px!important;}
hr{border-color:#0a2040!important;}
</style>
""", unsafe_allow_html=True)

# Session defaults
for k, v in {
    "mode": "register", "step": 1,
    "username": "",     "fractal_type": "mandelbrot",
    "fractal_markers": [], "behavior_data": {},
    "risk_result": {},  "auth_complete": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v
# ── Restore session from URL query parameters (Level 2 reload fix) ──
qp = st.query_params

if "username" in qp:
    st.session_state.username = qp["username"]

if "mode" in qp:
    st.session_state.mode = qp["mode"]

if "ftype" in qp:
    st.session_state.fractal_type = qp["ftype"]

if "step" in qp:
    try:
        st.session_state.step = int(qp["step"])
    except:
        pass

# IMPORTANT: Restore markers if sent from JS
if "markers" in qp:
    import json, urllib.parse
    try:
        parsed_markers = json.loads(urllib.parse.unquote(qp["markers"]))
        if len(parsed_markers) == 3:
            st.session_state.fractal_markers = parsed_markers
    except:
        pass
# Header
st.markdown("""
<div style="text-align:center;padding:20px 0 10px;">
  <div style="font-family:'Orbitron',monospace;font-size:2rem;font-weight:900;color:#00d4ff;
              letter-spacing:6px;text-shadow:0 0 30px rgba(0,212,255,0.6);">⬡ FRACTALAUTH</div>
  <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;color:#4a7a9b;
              letter-spacing:3px;margin-top:4px;">MULTI-LEVEL SECURE AUTHENTICATION SYSTEM</div>
</div>
""", unsafe_allow_html=True)

if st.session_state.auth_complete:
    from pages.dashboard import render_dashboard
    render_dashboard()
    st.stop()

# Mode toggle
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    mode = st.radio("Select mode", ["REGISTER", "LOGIN"],
                    index=0 if st.session_state.mode == "register" else 1,
                    horizontal=True, key="mode_radio", label_visibility="collapsed")
    new_mode = mode.lower()
    if new_mode != st.session_state.mode:
        st.session_state.mode            = new_mode
        st.session_state.step            = 1
        st.session_state.fractal_markers = []
        st.session_state.risk_result     = {}
        st.session_state.behavior_data   = {}
        st.rerun()

# Progress bar
step  = st.session_state.step
names = ["01 IDENTITY", "02 FRACTAL KEY", "03 PUZZLE"]
colors = ["#00ff88" if i+1 < step else "#00d4ff" if i+1 == step else "#1a3a55" for i in range(3)]
st.markdown(
    "<div style='display:flex;justify-content:space-between;margin:10px 0 4px;padding:0 5px;'>"
    + "".join(f"<span style='font-family:Share Tech Mono,monospace;font-size:0.6rem;"
              f"letter-spacing:1px;color:{c};'>{'✓ ' if i+1<step else ''}{n}</span>"
              for i,(n,c) in enumerate(zip(names,colors)))
    + "</div>",
    unsafe_allow_html=True
)
st.progress((step - 1) / (len(names) - 1))
st.markdown("<br>", unsafe_allow_html=True)

# Route to current step
if step == 1:
    from pages.level1_identity import render_level1
    render_level1()
elif step == 2:
    from pages.level2_fractal import render_level2
    render_level2()
elif step == 3:
    from pages.level5_puzzle import render_level5
    render_level5()
