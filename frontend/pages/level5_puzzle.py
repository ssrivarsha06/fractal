"""Level 5 — Risk Assessment + Authorization Puzzle"""

import streamlit as st
import streamlit.components.v1 as components
import requests
from datetime import datetime
from config import API_URL


def _panel(subtitle):
    st.markdown(f"""
    <div style="border:1px solid #0a2040;border-radius:4px;padding:22px;background:#060d16;
                position:relative;overflow:hidden;margin-bottom:15px;">
      <div style="position:absolute;top:0;left:0;right:0;height:2px;
                  background:linear-gradient(90deg,transparent,#00d4ff,transparent);"></div>
      <div style="font-family:'Orbitron',monospace;font-size:0.85rem;color:#00d4ff;
                  letter-spacing:3px;margin-bottom:4px;">⬡ LEVEL 05 — AUTHORIZATION PUZZLE</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#4a7a9b;">{subtitle}</div>
    </div>""", unsafe_allow_html=True)


def render_level5():
    if st.session_state.mode == "register":
        _render_register_complete()
    else:
        _render_login_puzzle()


# ─── REGISTRATION ────────────────────────────────────────────────────────────

def _render_register_complete():
    _panel("Registration nearly complete — confirm to finalise your account")
    st.markdown("""
    <div style="background:rgba(0,255,136,0.05);border:1px solid rgba(0,255,136,0.2);
                padding:14px;border-radius:2px;margin-bottom:20px;">
      <span style="font-family:'Share Tech Mono',monospace;font-size:0.78rem;color:#00ff88;">
        ✓ Fractal key saved · ✓ Behavioral profile recorded · ✓ Puzzles generated
      </span>
    </div>
    """, unsafe_allow_html=True)

    _sierpinski()

    col_b, _, col_d = st.columns([1, 2, 1])
    with col_b:
        if st.button("← BACK", key="l5_back_reg"):
            st.session_state.step = 2; st.rerun()
    with col_d:
        if st.button("COMPLETE REGISTRATION ✓", use_container_width=True):
            st.success("🎉 Account created! Switch to LOGIN to authenticate.")
            import time; time.sleep(1.2)
            st.session_state.mode            = "login"
            st.session_state.step            = 1
            st.session_state.fractal_markers = []
            st.session_state.behavior_data   = {}
            st.session_state.risk_result     = {}
            st.rerun()


# ─── LOGIN ───────────────────────────────────────────────────────────────────

def _render_login_puzzle():
    _panel("Complete the fractal-derived challenge to gain access")

    # Run risk assessment once
    if not st.session_state.risk_result:
        with st.spinner("⚙ Running background analysis (Level 3 + Level 4)…"):
            _run_risk_assessment()
        if not st.session_state.risk_result:
            return  # error was displayed inside

    risk = st.session_state.risk_result
    if risk.get("error"):
        st.error("Risk assessment failed. Please try again.")
        if st.button("RETRY"):
            st.session_state.risk_result = {}; st.rerun()
        return

    _risk_panel(risk)
    _sierpinski()

    # ── Puzzle ────────────────────────────────────────────────────────────
    puzzle = risk.get("puzzle", {})
    difficulty = risk.get("difficulty", "easy")
    badge_color = "#00ff88" if difficulty == "easy" else "#ff6b35"

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin:14px 0 10px;">
      <span style="font-family:'Orbitron',monospace;font-size:0.75rem;letter-spacing:2px;color:#00d4ff;">
        AUTHORIZATION PUZZLE</span>
      <span style="font-family:'Orbitron',monospace;font-size:0.58rem;padding:3px 10px;
                   border:1px solid {badge_color};color:{badge_color};border-radius:2px;">
        {difficulty.upper()} MODE</span>
    </div>
    <div style="border-left:3px solid #00d4ff;padding:11px 14px;
                background:rgba(0,212,255,0.04);margin-bottom:14px;
                font-family:'Orbitron',monospace;font-size:0.8rem;color:#00d4ff;">
      {puzzle.get('question','Loading…')}
    </div>
    """, unsafe_allow_html=True)

    options = puzzle.get("options", [])
    if options:
        choice = st.radio("SELECT YOUR ANSWER:", options, key="pz_ans",
                          label_visibility="visible")
        if puzzle.get("fractal_hint"):
            st.markdown(f'<div style="font-family:Share Tech Mono,monospace;font-size:0.67rem;'
                        f'color:#4a7a9b;margin-top:6px;">💡 {puzzle["fractal_hint"]}</div>',
                        unsafe_allow_html=True)

        col_b, _, col_v = st.columns([1, 2, 1])
        with col_b:
            if st.button("← BACK", key="l5_back_log"):
                st.session_state.step            = 2
                st.session_state.risk_result     = {}
                st.session_state.fractal_markers = []
                st.rerun()
        with col_v:
            if st.button("VERIFY ANSWER →", use_container_width=True, key="l5_verify"):
                _verify(choice)
    else:
        st.error("No puzzle options received. Please restart.")


def _run_risk_assessment():
    username = st.session_state.username
    beh      = st.session_state.get("behavior_data", {})
    hour     = datetime.now().hour
    try:
        r = requests.post(f"{API_URL}/login/risk-assessment", json={{
            "username":   username,
            "behavior": {{
                "username":         username,
                "mouse_speeds":     beh.get("mouse_speeds",    [0.3, 0.25, 0.28]),
                "pause_durations":  beh.get("pause_durations", [800, 1000, 600]),
                "click_count":      beh.get("click_count",     3),
                "zoom_count":       beh.get("zoom_count",      1),
                "fractal_time_ms":  beh.get("fractal_time_ms", 6000.0),
                "action_intervals": beh.get("action_intervals",[]),
            }},
            "ip_address": "192.168.1.1",
            "user_agent": "Streamlit",
            "login_hour": hour,
        }}, timeout=10)
        if r.status_code == 200:
            st.session_state.risk_result = r.json()
        else:
            st.error(r.json().get("detail","Risk assessment failed"))
            st.session_state.risk_result = {{"error": True}}
    except Exception as e:
        st.error(f"Backend error: {{e}}")
        st.session_state.risk_result = {{"error": True}}


def _verify(answer: str):
    username = st.session_state.username
    try:
        r = requests.post(f"{{API_URL}}/login/verify-puzzle",
                          json={{"username": username, "answer": answer}}, timeout=8)
        if r.status_code == 200:
            st.success("✅ Authentication complete!")
            import time; time.sleep(0.6)
            st.session_state.auth_complete = True
            st.rerun()
        else:
            st.error(r.json().get("detail","Incorrect answer — try again"))
    except Exception as e:
        st.error(f"Backend error: {{e}}")


def _risk_panel(risk: dict):
    b = risk.get("behavioral_risk",  0)
    c = risk.get("contextual_risk",  0)
    t = risk.get("composite_risk",   0)
    lv = risk.get("risk_level", "LOW")
    col = "#00ff88" if t < 30 else "#ff6b35" if t < 60 else "#ff3366"

    st.markdown(f"""
    <div style="background:#060d16;border:1px solid #0a2040;padding:16px;border-radius:2px;margin-bottom:14px;">
      <div style="font-family:'Share Tech Mono',monospace;font-size:0.62rem;letter-spacing:2px;
                  color:#4a7a9b;margin-bottom:10px;">COMPOSITE RISK — LEVEL 3 + LEVEL 4</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px;">
        <div style="text-align:center;">
          <div style="font-family:'Orbitron',monospace;font-size:1.3rem;color:#00d4ff;">{b}%</div>
          <div style="font-size:0.6rem;color:#4a7a9b;font-family:'Share Tech Mono',monospace;">BEHAVIORAL</div>
        </div>
        <div style="text-align:center;">
          <div style="font-family:'Orbitron',monospace;font-size:1.3rem;color:#00d4ff;">{c}%</div>
          <div style="font-size:0.6rem;color:#4a7a9b;font-family:'Share Tech Mono',monospace;">CONTEXTUAL</div>
        </div>
        <div style="text-align:center;">
          <div style="font-family:'Orbitron',monospace;font-size:1.3rem;color:{col};">{t}%</div>
          <div style="font-size:0.6rem;color:{col};font-family:'Share Tech Mono',monospace;">{lv}</div>
        </div>
      </div>
      <div style="height:5px;background:rgba(255,255,255,0.05);border-radius:3px;">
        <div style="height:100%;width:{t}%;background:{col};border-radius:3px;transition:width 0.5s;"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    all_logs = risk.get("behavioral_logs",[]) + risk.get("contextual_logs",[])
    if all_logs:
        with st.expander("🖥 BACKGROUND ANALYSIS LOG"):
            html = ""
            for log in all_logs:
                lv2 = log.get("level","OK")
                c2  = "#ff3366" if lv2=="RISK" else "#ff6b35" if lv2=="WARN" else "#00ff88"
                html += (f'<div style="font-family:Share Tech Mono,monospace;font-size:0.63rem;'
                         f'color:{c2};margin:2px 0;">[{lv2}] {log["msg"]}</div>')
            st.markdown(f'<div style="background:rgba(0,0,0,0.5);border:1px solid #0a2040;'
                        f'padding:10px;border-radius:2px;max-height:180px;overflow-y:auto;">{html}</div>',
                        unsafe_allow_html=True)


def _sierpinski():
    components.html("""
    <canvas id="sc" width="660" height="90"
            style="display:block;background:#020408;width:100%;margin:6px 0;"></canvas>
    <script>
    const s=document.getElementById('sc');
    const c=s.getContext('2d');
    c.fillStyle='#020408';c.fillRect(0,0,s.width,s.height);
    function t(x,y,sz,d){{
      if(d===0||sz<2){{
        c.beginPath();c.moveTo(x,y-sz);
        c.lineTo(x-sz*.866,y+sz*.5);c.lineTo(x+sz*.866,y+sz*.5);c.closePath();
        c.fillStyle=`rgba(0,212,255,${{.12+d*.04}})`;c.fill();
        c.strokeStyle='rgba(0,212,255,.35)';c.lineWidth=.5;c.stroke();return;
      }}
      t(x,y-sz/2,sz/2,d-1);t(x-sz*.433,y+sz*.25,sz/2,d-1);t(x+sz*.433,y+sz*.25,sz/2,d-1);
    }}
    for(let i=0;i<5;i++) t(66+i*132,78,50,4);
    </script>""", height=100)
