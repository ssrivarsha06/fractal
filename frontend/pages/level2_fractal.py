"""
Level 2 — Fractal Key Authentication

NO PAGE RELOAD APPROACH:
  - Fractal canvas is rendered above a hidden st.text_input
  - When user places 3rd marker, JS writes JSON into that text input
    via document.querySelector() inside the Streamlit DOM
  - A hidden st.button is then programmatically clicked by JS
  - Streamlit picks up the new text_input value + button click normally
  - No URL redirect, no session wipe, no reload
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import json
from config import API_URL


def _panel(subtitle):
    st.markdown(f"""
    <div style="border:1px solid #0a2040;border-radius:4px;padding:22px;background:#060d16;
                position:relative;overflow:hidden;margin-bottom:15px;">
      <div style="position:absolute;top:0;left:0;right:0;height:2px;
                  background:linear-gradient(90deg,transparent,#00d4ff,transparent);"></div>
      <div style="font-family:'Orbitron',monospace;font-size:0.85rem;color:#00d4ff;
                  letter-spacing:3px;margin-bottom:4px;">⬡ LEVEL 02 — FRACTAL KEY</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#4a7a9b;">
        {subtitle}
      </div>
    </div>""", unsafe_allow_html=True)


def render_level2():
    mode         = st.session_state.mode
    username     = st.session_state.username
    fractal_type = st.session_state.get("fractal_type", "mandelbrot")

    subtitle = (
        "Zoom & navigate. Click to place 3 secret markers — these become your fractal key."
        if mode == "register"
        else "Navigate to your registered regions. Place your 3 markers. (±0.08 tolerance)"
    )
    _panel(subtitle)

    # Fractal type selector (register only)
    if mode == "register":
        ftype = st.selectbox(
            "FRACTAL TYPE",
            ["mandelbrot", "julia"],
            index=0 if fractal_type == "mandelbrot" else 1,
            key="ftype_sel"
        )
        if ftype != st.session_state.fractal_type:
            st.session_state.fractal_type    = ftype
            st.session_state.fractal_markers = []
            st.rerun()
        fractal_type = ftype

    confirmed = st.session_state.get("fractal_markers", [])
    existing_json = json.dumps(confirmed)

    # ── THE KEY: hidden text input that JS will write into ────────────────────
    # We hide it with CSS via a wrapper div. JS finds it by the data-testid
    # Streamlit assigns, writes the JSON, then fires a rerun via clicking
    # the hidden submit button.
    st.markdown("""
    <style>
    div[data-testid="stTextInput"]:has(input[aria-label="fractal_data_input"]) {
        position: absolute !important;
        opacity: 0 !important;
        pointer-events: none !important;
        height: 0 !important;
        overflow: hidden !important;
    }
    div[data-testid="stButton"]:has(button[aria-label="fractal_submit_btn"]) {
        position: absolute !important;
        opacity: 0 !important;
        pointer-events: none !important;
        height: 0 !important;
        overflow: hidden !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Hidden text input — JS writes marker JSON here
    marker_input = st.text_input(
        "fractal_data_input",
        key="fractal_raw_input",
        label_visibility="hidden",
        value=""
    )

    # Hidden submit button — JS clicks this to trigger Streamlit rerun
    submit_clicked = st.button(
        "fractal_submit_btn",
        key="fractal_hidden_submit"
    )

    # If JS fired a submit, parse the input and save to session state
    if submit_clicked and marker_input:
        try:
            payload = json.loads(marker_input)
            markers  = payload.get("markers", [])
            behavior = payload.get("behavior", {})
            if len(markers) == 3:
                st.session_state.fractal_markers = markers
                beh = st.session_state.get("behavior_data", {})
                beh.update(behavior)
                st.session_state.behavior_data = beh
                # Clear the input so it doesn't re-trigger
                st.session_state.fractal_raw_input = ""
                st.rerun()
        except Exception:
            pass

    # ── Fractal canvas ────────────────────────────────────────────────────────
    components.html(
        _build_fractal_html(fractal_type, mode, existing_json),
        height=520,
        scrolling=False
    )

    # Show confirmed markers
    if confirmed:
        st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;color:#00ff88;
                    letter-spacing:2px;margin:8px 0 6px;">✓ MARKERS CAPTURED:</div>
        """, unsafe_allow_html=True)
        cols = st.columns(3)
        for i, (col, m) in enumerate(zip(cols, confirmed)):
            col.markdown(f"""
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;color:#00ff88;
                        padding:8px;border:1px solid rgba(0,255,136,0.3);border-radius:2px;
                        background:rgba(0,255,136,0.04);text-align:center;">
              <b>P{i+1}</b><br>Re: {m['fx']:.5f}<br>Im: {m['fy']:.5f}
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.68rem;color:#ff6b35;
                    padding:10px;border:1px solid rgba(255,107,53,0.3);border-radius:2px;
                    background:rgba(255,107,53,0.04);margin:8px 0;">
          ⚠ Click 3 spots on the fractal above to place your secret markers.
        </div>""", unsafe_allow_html=True)

    # Behavioral scan line
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin:10px 0;">
      <div style="width:6px;height:6px;border-radius:50%;background:#00ff88;
                  animation:blink 1s infinite;flex-shrink:0;"></div>
      <span style="font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#4a7a9b;">
        BEHAVIORAL METRICS RECORDING — timing, zoom pattern, click precision</span>
    </div>
    <style>@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}</style>
    """, unsafe_allow_html=True)

    # Navigation
    col_back, _, col_next = st.columns([1, 2, 1])
    with col_back:
        if st.button("← BACK", key="l2_back"):
            st.session_state.step            = 1
            st.session_state.fractal_markers = []
            st.rerun()
    with col_next:
        if st.button("CONFIRM KEY →", key="l2_next", use_container_width=True):
            if len(confirmed) < 3:
                st.error("Place 3 markers on the fractal first, then click CONFIRM KEY.")
            else:
                _submit_level2(confirmed)


def _submit_level2(markers):
    username     = st.session_state.username
    mode         = st.session_state.mode
    fractal_type = st.session_state.fractal_type
    beh          = st.session_state.get("behavior_data", {})

    if mode == "register":
        r = requests.post(f"{API_URL}/register/level2", json={
            "username": username, "fractal_type": fractal_type, "markers": markers,
        }, timeout=8)
        if r.status_code != 200:
            st.error(r.json().get("detail", "Failed to save fractal key"))
            return

        requests.post(f"{API_URL}/register/behavior", json={
            "username":         username,
            "mouse_speeds":     beh.get("mouse_speeds",     [0.3, 0.25, 0.28]),
            "pause_durations":  beh.get("pause_durations",  [800, 1000, 600]),
            "click_count":      beh.get("click_count",      3),
            "zoom_count":       beh.get("zoom_count",       1),
            "fractal_time_ms":  beh.get("fractal_time_ms",  5000.0),
            "action_intervals": beh.get("action_intervals", []),
        }, timeout=8)

        from utils.puzzle_gen import generate_puzzles
        easy, hard = generate_puzzles(markers)
        r2 = requests.post(f"{API_URL}/register/puzzles", json={
            "username": username, "easy_puzzle": easy, "hard_puzzle": hard,
        }, timeout=8)
        if r2.status_code == 200:
            st.session_state.step = 3
            st.rerun()
        else:
            st.error("Failed to save puzzles")
    else:
        r = requests.post(f"{API_URL}/login/level2", json={
            "username": username, "markers": markers,
        }, timeout=8)
        if r.status_code == 200:
            st.session_state.step = 3
            st.rerun()
        else:
            st.error(r.json().get("detail", "Fractal key mismatch — markers don't match registration"))


def _build_fractal_html(fractal_type: str, mode: str, existing_markers_json: str) -> str:
    fxmin = -2.5  if fractal_type == "mandelbrot" else -1.8
    fxmax =  1.0  if fractal_type == "mandelbrot" else  1.8
    fymin = -1.25 if fractal_type == "mandelbrot" else -1.2
    fymax =  1.25 if fractal_type == "mandelbrot" else  1.2

    init_status = (
        "Lock LOGIN: Navigate to your registered regions and place your 3 markers."
        if mode == "login"
        else "Register: Choose 3 memorable spots and click to mark them."
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#020408;color:#c8e6ff;font-family:'Share Tech Mono',monospace;overflow:hidden;padding:4px;}}
canvas{{display:block;cursor:crosshair;border:1px solid #0a2040;width:100%;}}
.ctrl{{display:flex;gap:6px;padding:6px 0;flex-wrap:wrap;align-items:center;}}
.btn{{padding:6px 14px;background:rgba(0,212,255,0.06);color:#00d4ff;border:1px solid #00d4ff;
      border-radius:2px;cursor:pointer;font-family:inherit;font-size:0.65rem;letter-spacing:1px;}}
.btn:hover{{background:rgba(0,212,255,0.16);}}
.btn.red{{color:#ff3366;border-color:#ff3366;background:rgba(255,51,102,0.06);}}
.coords{{font-size:0.68rem;color:#00d4ff;padding:5px 10px;background:rgba(0,212,255,0.04);
         border:1px solid #0a2040;border-radius:2px;margin-top:5px;}}
.tags{{display:flex;flex-wrap:wrap;gap:5px;margin-top:5px;}}
.tag{{font-size:0.62rem;color:#00ff88;padding:2px 7px;border:1px solid rgba(0,255,136,0.3);
      border-radius:2px;background:rgba(0,255,136,0.05);}}
.status{{font-size:0.63rem;color:#4a7a9b;margin-top:5px;min-height:16px;}}
.status.ok{{color:#00ff88;font-weight:bold;}}
</style>
</head>
<body>
<div class="ctrl">
  <button class="btn" onclick="zoomIn()">ZOOM IN +</button>
  <button class="btn" onclick="zoomOut()">ZOOM OUT -</button>
  <button class="btn" onclick="resetView()">RESET VIEW</button>
  <button class="btn red" onclick="clearMarkers()">CLEAR MARKERS</button>
  <span id="mc" style="font-size:0.63rem;color:#4a7a9b;margin-left:6px;">Markers: 0 / 3</span>
</div>
<canvas id="fc" height="370"></canvas>
<div class="coords" id="coords">Hover over fractal to see coordinates...</div>
<div class="tags" id="tags"></div>
<div class="status" id="status">{init_status}</div>

<script>
const canvas = document.getElementById('fc');
const ctx    = canvas.getContext('2d');
canvas.width = canvas.parentElement ? canvas.parentElement.offsetWidth : 660;

let S = {{
  type:'{fractal_type}', xMin:{fxmin}, xMax:{fxmax}, yMin:{fymin}, yMax:{fymax},
  markers:[], busy:false
}};

// Pre-load markers already confirmed by Python
const preloaded = {existing_markers_json};
if (Array.isArray(preloaded) && preloaded.length > 0) {{
  S.markers = preloaded.map(m => ({{fx:m.fx, fy:m.fy}}));
}}

let B = {{ speeds:[], pauses:[], clicks:0, zooms:0,
           lastPos:null, lastTime:null, lastAct:Date.now(), t0:Date.now() }};

// ── Fractal math ───────────────────────────────────────────
function mandelbrot(cx,cy,mi) {{
  let x=0,y=0,i=0;
  while(x*x+y*y<=4&&i<mi){{const t=x*x-y*y+cx;y=2*x*y+cy;x=t;i++;}} return i;
}}
function julia(zx,zy,cx,cy,mi) {{
  let i=0;
  while(zx*zx+zy*zy<=4&&i<mi){{const t=zx*zx-zy*zy+cx;zy=2*zx*zy+cy;zx=t;i++;}} return i;
}}
function colorOf(i,mi) {{
  if(i===mi) return [2,6,15];
  const t=i/mi;
  return [Math.min(255,Math.floor(9*(1-t)*t*t*t*255)+10),
          Math.min(255,Math.floor(15*(1-t)*(1-t)*t*t*255)+40),
          Math.min(255,Math.floor(8.5*(1-t)**3*t*255)+80)];
}}
function render() {{
  if(S.busy) return; S.busy=true;
  const W=canvas.width, H=canvas.height;
  const img=ctx.createImageData(W,H); const mi=80;
  for(let py=0;py<H;py++) {{
    for(let px=0;px<W;px++) {{
      const cx=S.xMin+(px/W)*(S.xMax-S.xMin);
      const cy=S.yMin+(py/H)*(S.yMax-S.yMin);
      const it=S.type==='mandelbrot'?mandelbrot(cx,cy,mi):julia(cx,cy,-0.7,0.27,mi);
      const [r,g,b]=colorOf(it,mi);
      const idx=(py*W+px)*4;
      img.data[idx]=r;img.data[idx+1]=g;img.data[idx+2]=b;img.data[idx+3]=255;
    }}
  }}
  ctx.putImageData(img,0,0); drawMarkers(); S.busy=false;
}}
function drawMarkers() {{
  const W=canvas.width,H=canvas.height;
  S.markers.forEach((m,i)=>{{
    const px=((m.fx-S.xMin)/(S.xMax-S.xMin))*W;
    const py=((m.fy-S.yMin)/(S.yMax-S.yMin))*H;
    ctx.beginPath();ctx.arc(px,py,8,0,Math.PI*2);
    ctx.strokeStyle='#00ff88';ctx.lineWidth=2;ctx.stroke();
    ctx.beginPath();ctx.moveTo(px-13,py);ctx.lineTo(px+13,py);
    ctx.moveTo(px,py-13);ctx.lineTo(px,py+13);
    ctx.strokeStyle='rgba(0,255,136,0.5)';ctx.lineWidth=1;ctx.stroke();
    ctx.fillStyle='#00ff88';ctx.font='bold 11px monospace';
    ctx.fillText('P'+(i+1),px+10,py-9);
  }});
}}

// ── Controls ───────────────────────────────────────────────
function zoom(f) {{
  const cx=(S.xMin+S.xMax)/2,cy=(S.yMin+S.yMax)/2;
  const hw=(S.xMax-S.xMin)*f/2,hh=(S.yMax-S.yMin)*f/2;
  S.xMin=cx-hw;S.xMax=cx+hw;S.yMin=cy-hh;S.yMax=cy+hh;
  B.zooms++;B.pauses.push(Date.now()-B.lastAct);B.lastAct=Date.now();render();
}}
function zoomIn()    {{ zoom(0.5); }}
function zoomOut()   {{ zoom(1.6); }}
function resetView() {{ S.xMin={fxmin};S.xMax={fxmax};S.yMin={fymin};S.yMax={fymax};render(); }}
function clearMarkers() {{ S.markers=[];updateUI();render(); }}

canvas.addEventListener('mousemove',e=>{{
  const r=canvas.getBoundingClientRect();
  const px=(e.clientX-r.left)*(canvas.width/r.width);
  const py=(e.clientY-r.top)*(canvas.height/r.height);
  const fx=S.xMin+(px/canvas.width)*(S.xMax-S.xMin);
  const fy=S.yMin+(py/canvas.height)*(S.yMax-S.yMin);
  document.getElementById('coords').textContent=`Re: ${{fx.toFixed(6)}}  Im: ${{fy.toFixed(6)}}`;
  const now=Date.now();
  if(B.lastPos){{
    const dx=e.clientX-B.lastPos.x,dy=e.clientY-B.lastPos.y,dt=now-B.lastTime;
    if(dt>0)B.speeds.push(Math.sqrt(dx*dx+dy*dy)/dt);
  }}
  B.lastPos={{x:e.clientX,y:e.clientY}};B.lastTime=now;
}});

canvas.addEventListener('click',e=>{{
  if(S.markers.length>=3){{
    setStatus('Max 3 markers. Use CLEAR MARKERS to restart.','');return;
  }}
  const r=canvas.getBoundingClientRect();
  const px=(e.clientX-r.left)*(canvas.width/r.width);
  const py=(e.clientY-r.top)*(canvas.height/r.height);
  const fx=S.xMin+(px/canvas.width)*(S.xMax-S.xMin);
  const fy=S.yMin+(py/canvas.height)*(S.yMax-S.yMin);
  S.markers.push({{fx,fy}});
  B.clicks++;B.pauses.push(Date.now()-B.lastAct);B.lastAct=Date.now();
  updateUI();render();
  if(S.markers.length===3) sendToStreamlit();
}});

function updateUI() {{
  document.getElementById('mc').textContent=`Markers: ${{S.markers.length}} / 3`;
  document.getElementById('tags').innerHTML=S.markers.map((m,i)=>
    `<span class="tag">P${{i+1}}: (${{m.fx.toFixed(4)}}, ${{m.fy.toFixed(4)}})</span>`).join('');
}}
function setStatus(msg,cls) {{
  const el=document.getElementById('status');el.textContent=msg;el.className='status '+cls;
}}

// ── Send to Streamlit — NO PAGE RELOAD ────────────────────
// We write marker JSON into the hidden st.text_input above this iframe,
// then programmatically click the hidden st.button to trigger a Streamlit rerun.
// Streamlit reads the new input value via st.session_state normally.
function sendToStreamlit() {{
  setStatus('✓ 3 markers captured — proceeding to next level...', 'ok');

  const payload = JSON.stringify({{
    markers: S.markers,
    behavior: {{
      mouse_speeds:    B.speeds.slice(-60),
      pause_durations: B.pauses,
      click_count:     B.clicks,
      zoom_count:      B.zooms,
      fractal_time_ms: Date.now()-B.t0,
      action_intervals:B.pauses,
    }}
  }});

  // Walk up to the parent Streamlit document and find our hidden elements
  const doc = window.parent.document;

  // Find the hidden text input — Streamlit renders it with the aria-label = key name
  // The input element will have aria-label matching our key "fractal_data_input"
  // but Streamlit actually uses the label text, so we search by placeholder or just
  // find all text inputs and pick the one with our specific key via data attributes.
  // Most reliable: find by the label text we set ("fractal_data_input")
  let targetInput = null;
  const allInputs = doc.querySelectorAll('input[type="text"], input:not([type])');
  for (const inp of allInputs) {{
    // Streamlit hides label in a <label> tag nearby; check aria-label too
    if (inp.getAttribute('aria-label') === 'fractal_data_input') {{
      targetInput = inp; break;
    }}
  }}
  // Fallback: find by checking the surrounding label text
  if (!targetInput) {{
    const labels = doc.querySelectorAll('label');
    for (const lbl of labels) {{
      if (lbl.textContent.trim() === 'fractal_data_input') {{
        targetInput = lbl.closest('[data-testid="stTextInput"]')?.querySelector('input');
        if (targetInput) break;
      }}
    }}
  }}

  if (!targetInput) {{
    setStatus('ERROR: Could not find Streamlit input. Please use manual entry below.','');
    return;
  }}

  // Set the value using React's internal setter so Streamlit detects the change
  const nativeInputSetter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, 'value'
  ).set;
  nativeInputSetter.call(targetInput, payload);
  targetInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
  targetInput.dispatchEvent(new Event('change', {{ bubbles: true }}));

  // Now find and click the hidden submit button
setTimeout(() => {{
    const allBtns = doc.querySelectorAll('[data-testid="stButton"] button');
    for (const btn of allBtns) {{
        if (btn.innerText.includes('fractal_submit_btn')) {{
            btn.click();
            return;
        }}
    }}

    // Fallback: try aria-label
    const btn2 = doc.querySelector('button[aria-label="fractal_submit_btn"]');
    if (btn2) btn2.click();
}}, 300);
}}

// Init
render();
updateUI();
if (S.markers.length===3) setStatus('✓ Markers loaded. Click CONFIRM KEY below.','ok');
</script>
</body>
</html>"""
