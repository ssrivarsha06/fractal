"""Dashboard — shown after successful full authentication"""

import streamlit as st


def render_dashboard():
    username = st.session_state.get("username", "USER")
    risk     = st.session_state.get("risk_result", {})
    comp     = risk.get("composite_risk", 0)
    level    = risk.get("risk_level", "LOW")
    diff     = risk.get("difficulty", "easy")
    col      = "#00ff88" if comp < 30 else "#ff6b35" if comp < 60 else "#ff3366"

    st.markdown(f"""
    <div style="border:1px solid #0a2040;border-radius:4px;padding:22px;background:#060d16;
                position:relative;overflow:hidden;margin-bottom:20px;">
      <div style="position:absolute;top:0;left:0;right:0;height:2px;
                  background:linear-gradient(90deg,#00ff88,#00d4ff,#ff6b35);"></div>
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
        <div>
          <div style="font-family:'Orbitron',monospace;font-size:1.1rem;color:#00ff88;letter-spacing:3px;">
            ✓ ACCESS GRANTED</div>
          <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#4a7a9b;margin-top:4px;">
            {username.upper()} — FractalAuth Multi-Level Security</div>
        </div>
        <div style="font-family:'Orbitron',monospace;font-size:0.58rem;padding:6px 14px;
                    border:1px solid #00ff88;color:#00ff88;border-radius:2px;letter-spacing:2px;">
          LEVEL 5 — FULL ACCESS</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Balance",        "₹ 84,203",  "+2.3%")
    c2.metric("Security Level", "LVL 5",     "Full Access")
    c3.metric("Risk Score",     f"{comp}%",  level)
    c4.metric("Puzzle Mode",    diff.title(), "Passed ✓")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div style="font-family:Orbitron,monospace;font-size:0.72rem;color:#00d4ff;'
                'letter-spacing:2px;margin-bottom:10px;">AUTH SUMMARY</div>', unsafe_allow_html=True)

    rows = [
        ("Level 1", "Identity Verification",            "✓ Passed",                       "#00ff88"),
        ("Level 2", "Fractal Key Authentication",       "✓ Passed",                       "#00ff88"),
        ("Level 3", "Behavioral Analysis (Background)", f"✓ Risk {risk.get('behavioral_risk',0)}%","#00ff88"),
        ("Level 4", "Contextual Risk (Background)",     f"✓ Risk {risk.get('contextual_risk',0)}%","#00ff88"),
        ("Level 5", "Authorization Puzzle",             f"✓ {diff.title()} mode passed",  "#00ff88"),
    ]
    for lv, name, status, c in rows:
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:9px 14px;'
            f'border:1px solid #0a2040;border-radius:2px;margin-bottom:5px;'
            f'background:rgba(0,255,136,0.02);">'
            f'<span style="font-family:Orbitron,monospace;font-size:0.65rem;color:#4a7a9b;">{lv}</span>'
            f'<span style="font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#c8e6ff;">{name}</span>'
            f'<span style="font-family:Share Tech Mono,monospace;font-size:0.68rem;color:{c};">{status}</span>'
            f'</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("LOGOUT"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
