"""Level 1 — Identity Verification"""
import re, time, requests, streamlit as st
from config import API_URL


def _pw_check(pw):
    errs = []
    if len(pw) < 8:            errs.append("8+ chars")
    if not re.search(r"[A-Z]", pw): errs.append("uppercase")
    if not re.search(r"[0-9]", pw): errs.append("number")
    if not re.search(r"[!@#$%^&*()\-_=+\[\]{};:'\",.<>/?\\|`~]", pw): errs.append("symbol")
    return (not errs), ("Missing: " + ", ".join(errs) if errs else "✓ Password OK")


def _box(title, subtitle):
    st.markdown(f"""
    <div style="border:1px solid #0a2040;border-radius:4px;padding:22px;background:#060d16;
                position:relative;overflow:hidden;margin-bottom:18px;">
      <div style="position:absolute;top:0;left:0;right:0;height:2px;
                  background:linear-gradient(90deg,transparent,#00d4ff,transparent);"></div>
      <div style="font-family:'Orbitron',monospace;font-size:0.85rem;color:#00d4ff;
                  letter-spacing:3px;margin-bottom:4px;">{title}</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#4a7a9b;">{subtitle}</div>
    </div>""", unsafe_allow_html=True)


def render_level1():
    if st.session_state.mode == "register":
        _box("⬡ LEVEL 01 — IDENTITY VERIFICATION", "Create your secure account credentials")
        _register()
    else:
        _box("⬡ LEVEL 01 — IDENTITY VERIFICATION", "Enter your credentials to begin verification")
        _login()


def _register():
    c1, c2 = st.columns(2)
    username = c1.text_input("USERNAME", placeholder="john_doe_42", key="ru")
    email    = c2.text_input("EMAIL",    placeholder="user@domain.com", key="re")

    c3, c4 = st.columns(2)
    password = c3.text_input("PASSWORD", type="password", placeholder="Min 8 chars", key="rp")
    confirm  = c4.text_input("CONFIRM PASSWORD", type="password", placeholder="Repeat", key="rc")

    if password:
        ok, msg = _pw_check(password)
        st.markdown(f'<p style="font-family:Share Tech Mono,monospace;font-size:0.65rem;'
                    f'color:{"#00ff88" if ok else "#ff3366"};">{msg}</p>', unsafe_allow_html=True)
    if confirm and password:
        match = password == confirm
        st.markdown(f'<p style="font-family:Share Tech Mono,monospace;font-size:0.65rem;'
                    f'color:{"#00ff88" if match else "#ff3366"};">'
                    f'{"✓ Passwords match" if match else "✗ Passwords do not match"}</p>',
                    unsafe_allow_html=True)

    _scan_line()
    _, col = st.columns([3, 1])
    if col.button("PROCEED →", use_container_width=True, key="l1_reg_go"):
        ok, msg = _pw_check(password)
        if not username:       st.error("Username required"); return
        if not email or "@" not in email: st.error("Valid email required"); return
        if not ok:             st.error(msg); return
        if password != confirm: st.error("Passwords do not match"); return
        try:
            r = requests.post(f"{API_URL}/register/level1",
                              json={"username": username, "email": email, "password": password},
                              timeout=8)
            if r.status_code == 200:
                st.session_state.username      = username
                st.session_state.behavior_data = {"session_start": time.time()}
                st.session_state.step          = 2
                st.rerun()
            else:
                st.error(r.json().get("detail", "Registration failed"))
        except Exception as e:
            st.error(f"Cannot reach backend: {e}")


def _login():
    username = st.text_input("USERNAME", key="lu")
    password = st.text_input("PASSWORD", type="password", key="lp")
    _scan_line()
    _, col = st.columns([3, 1])
    if col.button("PROCEED →", use_container_width=True, key="l1_log_go"):
        if not username or not password: st.error("All fields required"); return
        try:
            r = requests.post(f"{API_URL}/login/level1",
                              json={"username": username, "password": password}, timeout=8)
            if r.status_code == 200:
                st.session_state.username      = username
                st.session_state.fractal_type  = r.json()["fractal_type"]
                st.session_state.behavior_data = {"session_start": time.time()}
                st.session_state.step          = 2
                st.rerun()
            else:
                st.error(r.json().get("detail", "Login failed"))
        except Exception as e:
            st.error(f"Cannot reach backend: {e}")


def _scan_line():
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin:10px 0;">
      <div style="width:6px;height:6px;border-radius:50%;background:#00ff88;
                  animation:blink 1s infinite;"></div>
      <span style="font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#4a7a9b;">
        BEHAVIORAL ANALYSIS ACTIVE — session tracking started</span>
    </div>
    <style>@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}</style>
    """, unsafe_allow_html=True)
