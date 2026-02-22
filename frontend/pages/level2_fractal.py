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

    # ── Read markers + behavior from query params (set by iframe JS) ─────────
    qp = st.query_params
    if "fractal_markers" in qp:
        try:
            raw  = qp["fractal_markers"]
            data = json.loads(raw)
            markers = data.get("markers", [])
            beh     = data.get("behavior", {})

            # Only accept if we have real data (not empty defaults)
            if (
                len(markers) == 3
                and isinstance(beh.get("mouse_speeds"), list)
                and len(beh.get("mouse_speeds", [])) > 0
            ):
                st.session_state.fractal_markers = markers
                st.session_state.behavior_data   = beh
                st.query_params.pop("fractal_markers", None)
                st.rerun()
        except Exception:
            pass

    subtitle = (
        "Zoom & navigate. Click to place 3 secret markers — these become your fractal key."
        if mode == "register"
        else "Navigate to your registered regions. Place your 3 markers. (±0.08 tolerance)"
    )
    _panel(subtitle)

    if mode == "register":
        ftype = st.selectbox(
            "FRACTAL TYPE", ["mandelbrot", "julia"],
            index=0 if fractal_type == "mandelbrot" else 1,
            key="ftype_sel",
        )
        if ftype != st.session_state.get("fractal_type", "mandelbrot"):
            st.session_state.fractal_type    = ftype
            st.session_state.fractal_markers = []
            st.session_state.behavior_data   = {}
            st.rerun()
        fractal_type = ftype

    confirmed     = st.session_state.get("fractal_markers", [])
    existing_json = json.dumps(confirmed)

    components.html(
        _build_fractal_html(fractal_type, mode, existing_json),
        height=540,
        scrolling=False,
    )

    # ── Live behavioral data preview ─────────────────────────────────────────
    beh = st.session_state.get("behavior_data", {})
    _show_behavior_live(beh)

    # ── Marker display ───────────────────────────────────────────────────────
    if confirmed:
        st.markdown(
            '<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.65rem;'
            'color:#00ff88;letter-spacing:2px;margin:8px 0 6px;">✓ MARKERS CAPTURED:</div>',
            unsafe_allow_html=True,
        )
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
            ⚠ Click 3 spots on the fractal above to place your markers.
        </div>""", unsafe_allow_html=True)

    # ── Recording indicator ──────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin:10px 0;">
      <div style="width:6px;height:6px;border-radius:50%;background:#00ff88;
                  animation:blink 1s infinite;flex-shrink:0;"></div>
      <span style="font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#4a7a9b;">
        BEHAVIORAL METRICS RECORDING — mouse speed · click timing · zoom pattern · inter-click intervals
      </span>
    </div>
    <style>@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}</style>
    """, unsafe_allow_html=True)

    col_back, _, col_next = st.columns([1, 2, 1])
    with col_back:
        if st.button("← BACK", key="l2_back"):
            st.session_state.step            = 1
            st.session_state.fractal_markers = []
            st.session_state.behavior_data   = {}
            st.query_params.clear()
            st.rerun()
    with col_next:
        if st.button("CONFIRM KEY →", key="l2_next", use_container_width=True):
            if len(confirmed) < 3:
                st.error("Place 3 markers on the fractal first.")
            else:
                _submit_level2(confirmed)


def _show_behavior_live(beh: dict):
    """Shows a live mini-panel of captured behavioral metrics."""
    if not beh:
        return

    speeds    = beh.get("mouse_speeds", [])
    pauses    = beh.get("pause_durations", [])
    clicks    = beh.get("click_count", 0)
    zooms     = beh.get("zoom_count", 0)
    t_ms      = beh.get("fractal_time_ms", 0)
    intervals = beh.get("action_intervals", [])

    avg_speed    = round(sum(speeds) / len(speeds), 4)       if speeds    else 0
    avg_pause    = round(sum(pauses) / len(pauses), 1)       if pauses    else 0
    avg_interval = round(sum(intervals) / len(intervals), 1) if intervals else 0

    st.markdown(f"""
    <div style="background:#060d16;border:1px solid #0a2040;padding:12px 16px;
                border-radius:2px;margin:8px 0 4px;">
      <div style="font-family:'Share Tech Mono',monospace;font-size:0.58rem;
                  color:#4a7a9b;letter-spacing:2px;margin-bottom:8px;">
        ◈ CAPTURED BEHAVIORAL PROFILE
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
        <div style="text-align:center;">
          <div style="font-family:'Orbitron',monospace;font-size:1rem;color:#00d4ff;">{avg_speed}</div>
          <div style="font-size:0.55rem;color:#4a7a9b;font-family:'Share Tech Mono',monospace;">AVG MOUSE SPEED</div>
        </div>
        <div style="text-align:center;">
          <div style="font-family:'Orbitron',monospace;font-size:1rem;color:#00d4ff;">{avg_pause}ms</div>
          <div style="font-size:0.55rem;color:#4a7a9b;font-family:'Share Tech Mono',monospace;">AVG PAUSE</div>
        </div>
        <div style="text-align:center;">
          <div style="font-family:'Orbitron',monospace;font-size:1rem;color:#00d4ff;">{avg_interval}ms</div>
          <div style="font-size:0.55rem;color:#4a7a9b;font-family:'Share Tech Mono',monospace;">AVG CLICK INTERVAL</div>
        </div>
        <div style="text-align:center;">
          <div style="font-family:'Orbitron',monospace;font-size:1rem;color:#00ff88;">{clicks}</div>
          <div style="font-size:0.55rem;color:#4a7a9b;font-family:'Share Tech Mono',monospace;">TOTAL CLICKS</div>
        </div>
        <div style="text-align:center;">
          <div style="font-family:'Orbitron',monospace;font-size:1rem;color:#00ff88;">{zooms}</div>
          <div style="font-size:0.55rem;color:#4a7a9b;font-family:'Share Tech Mono',monospace;">ZOOM EVENTS</div>
        </div>
        <div style="text-align:center;">
          <div style="font-family:'Orbitron',monospace;font-size:1rem;color:#00ff88;">{round(t_ms/1000,1)}s</div>
          <div style="font-size:0.55rem;color:#4a7a9b;font-family:'Share Tech Mono',monospace;">TIME ON FRACTAL</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


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

        # Send REAL behavioral data — no hardcoded fallbacks
        r_beh = requests.post(f"{API_URL}/register/behavior", json={
            "username":         username,
            "mouse_speeds":     beh.get("mouse_speeds",     []),
            "pause_durations":  beh.get("pause_durations",  []),
            "click_count":      beh.get("click_count",      0),
            "zoom_count":       beh.get("zoom_count",       0),
            "fractal_time_ms":  beh.get("fractal_time_ms",  0.0),
            "action_intervals": beh.get("action_intervals", []),
        }, timeout=8)
        if r_beh.status_code != 200:
            st.warning("Behavioral profile save failed — continuing anyway.")

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
        # Login: send real behavior alongside marker verification
        r = requests.post(f"{API_URL}/login/level2", json={
            "username": username,
            "markers":  markers,
            "behavior": {
                "username":         username,
                "mouse_speeds":     beh.get("mouse_speeds",     []),
                "pause_durations":  beh.get("pause_durations",  []),
                "click_count":      beh.get("click_count",      0),
                "zoom_count":       beh.get("zoom_count",       0),
                "fractal_time_ms":  beh.get("fractal_time_ms",  0.0),
                "action_intervals": beh.get("action_intervals", []),
            },
        }, timeout=8)
        if r.status_code == 200:
            st.session_state.step = 3
            st.rerun()
        else:
            st.error(r.json().get("detail", "Fractal key mismatch"))


def _build_fractal_html(fractal_type: str, mode: str, existing_markers_json: str) -> str:
    fxmin = -2.5 if fractal_type == "mandelbrot" else -1.8
    fxmax =  1.0 if fractal_type == "mandelbrot" else  1.8
    fymin = -1.25 if fractal_type == "mandelbrot" else -1.2
    fymax =  1.25 if fractal_type == "mandelbrot" else  1.2
    init_status = (
        "Navigate to your registered regions and place your 3 markers."
        if mode == "login"
        else "Choose 3 memorable spots and click to mark them."
    )

    return f"""<!DOCTYPE html><html><head><style>
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
.beh-bar{{display:grid;grid-template-columns:repeat(6,1fr);gap:4px;margin-top:6px;}}
.beh-cell{{text-align:center;background:rgba(0,212,255,0.04);border:1px solid #0a2040;
           padding:3px 2px;border-radius:2px;}}
.beh-val{{font-size:0.68rem;color:#00d4ff;font-family:monospace;}}
.beh-lbl{{font-size:0.46rem;color:#4a7a9b;}}
</style></head><body>
<div class="ctrl">
  <button class="btn" onclick="zoomIn()">ZOOM IN +</button>
  <button class="btn" onclick="zoomOut()">ZOOM OUT -</button>
  <button class="btn" onclick="resetView()">RESET VIEW</button>
  <button class="btn red" onclick="clearMarkers()">CLEAR MARKERS</button>
  <span id="mc" style="font-size:0.63rem;color:#4a7a9b;margin-left:6px;">Markers: 0 / 3</span>
</div>
<canvas id="fc" height="350"></canvas>
<div class="coords" id="coords">Hover over fractal to see coordinates...</div>
<div class="tags"   id="tags"></div>

<!-- Live behavioral mini-bar inside the iframe -->
<div class="beh-bar">
  <div class="beh-cell"><div class="beh-val" id="b_spd">0</div><div class="beh-lbl">AVG SPEED</div></div>
  <div class="beh-cell"><div class="beh-val" id="b_pau">0ms</div><div class="beh-lbl">AVG PAUSE</div></div>
  <div class="beh-cell"><div class="beh-val" id="b_int">0ms</div><div class="beh-lbl">CLK INTRVL</div></div>
  <div class="beh-cell"><div class="beh-val" id="b_clk">0</div><div class="beh-lbl">CLICKS</div></div>
  <div class="beh-cell"><div class="beh-val" id="b_zm">0</div><div class="beh-lbl">ZOOMS</div></div>
  <div class="beh-cell"><div class="beh-val" id="b_tm">0s</div><div class="beh-lbl">TIME</div></div>
</div>
<div class="status" id="status">{init_status}</div>

<script>
// ── Canvas setup ─────────────────────────────────────────────────────────────
const canvas = document.getElementById('fc');
const ctx    = canvas.getContext('2d');
canvas.width = canvas.parentElement ? canvas.parentElement.offsetWidth : 660;

let S = {{
  type: '{fractal_type}',
  xMin: {fxmin}, xMax: {fxmax},
  yMin: {fymin}, yMax: {fymax},
  markers: [],
  busy: false
}};

// Pre-load existing markers if any
const preloaded = {existing_markers_json};
if (Array.isArray(preloaded) && preloaded.length > 0)
  S.markers = preloaded.map(m => ({{fx: m.fx, fy: m.fy}}));

// ── Behavioral state ─────────────────────────────────────────────────────────
let B = {{
  speeds:          [],   // rolling px/ms samples from mousemove
  pauseDurations:  [],   // inactivity gaps > 300ms
  actionIntervals: [],   // ms between consecutive clicks
  clickTimes:      [],   // timestamps of each click
  clicks:          0,
  zooms:           0,
  lastMovePos:     null,
  lastMoveTime:    null,
  lastClickTime:   null,
  lastActivityAt:  Date.now(),
  t0:              Date.now(),
}};

// ── Pause detector: polls every 500ms, records gaps > 300ms ──────────────────
setInterval(() => {{
  const gap = Date.now() - B.lastActivityAt;
  if (gap > 300 && gap < 20000) {{
    B.pauseDurations.push(gap);
  }}
}}, 500);

// ── Live behavioral bar updater ───────────────────────────────────────────────
setInterval(() => {{
  const avg = arr => arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : 0;
  document.getElementById('b_spd').textContent = avg(B.speeds).toFixed(3);
  document.getElementById('b_pau').textContent = Math.round(avg(B.pauseDurations)) + 'ms';
  document.getElementById('b_int').textContent = Math.round(avg(B.actionIntervals)) + 'ms';
  document.getElementById('b_clk').textContent = B.clicks;
  document.getElementById('b_zm').textContent  = B.zooms;
  document.getElementById('b_tm').textContent  = ((Date.now()-B.t0)/1000).toFixed(1) + 's';
}}, 800);

// ── Fractal math ─────────────────────────────────────────────────────────────
function mandelbrot(cx, cy, mi) {{
  let x=0, y=0, i=0;
  while (x*x+y*y<=4 && i<mi) {{
    const t=x*x-y*y+cx; y=2*x*y+cy; x=t; i++;
  }}
  return i;
}}
function julia(zx, zy, cx, cy, mi) {{
  let i=0;
  while (zx*zx+zy*zy<=4 && i<mi) {{
    const t=zx*zx-zy*zy+cx; zy=2*zx*zy+cy; zx=t; i++;
  }}
  return i;
}}
function colorOf(i, mi) {{
  if (i===mi) return [2,6,15];
  const t=i/mi;
  return [
    Math.min(255,Math.floor(9*(1-t)*t*t*t*255)+10),
    Math.min(255,Math.floor(15*(1-t)*(1-t)*t*t*255)+40),
    Math.min(255,Math.floor(8.5*(1-t)**3*t*255)+80),
  ];
}}

// ── Render fractal ────────────────────────────────────────────────────────────
function render() {{
  if (S.busy) return;
  S.busy = true;
  const W=canvas.width, H=canvas.height, img=ctx.createImageData(W,H), mi=80;
  for (let py=0; py<H; py++) {{
    for (let px=0; px<W; px++) {{
      const cx=S.xMin+(px/W)*(S.xMax-S.xMin);
      const cy=S.yMin+(py/H)*(S.yMax-S.yMin);
      const it=S.type==='mandelbrot'?mandelbrot(cx,cy,mi):julia(cx,cy,-0.7,0.27,mi);
      const [r,g,b]=colorOf(it,mi);
      const idx=(py*W+px)*4;
      img.data[idx]=r; img.data[idx+1]=g; img.data[idx+2]=b; img.data[idx+3]=255;
    }}
  }}
  ctx.putImageData(img,0,0);
  drawMarkers();
  S.busy=false;
}}

function drawMarkers() {{
  const W=canvas.width, H=canvas.height;
  S.markers.forEach((m,i) => {{
    const px=((m.fx-S.xMin)/(S.xMax-S.xMin))*W;
    const py=((m.fy-S.yMin)/(S.yMax-S.yMin))*H;
    ctx.beginPath(); ctx.arc(px,py,8,0,Math.PI*2);
    ctx.strokeStyle='#00ff88'; ctx.lineWidth=2; ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(px-13,py); ctx.lineTo(px+13,py);
    ctx.moveTo(px,py-13); ctx.lineTo(px,py+13);
    ctx.strokeStyle='rgba(0,255,136,0.5)'; ctx.lineWidth=1; ctx.stroke();
    ctx.fillStyle='#00ff88'; ctx.font='bold 11px monospace';
    ctx.fillText('P'+(i+1),px+10,py-9);
  }});
}}

// ── Zoom ──────────────────────────────────────────────────────────────────────
function zoom(f) {{
  const cx=(S.xMin+S.xMax)/2, cy=(S.yMin+S.yMax)/2;
  const hw=(S.xMax-S.xMin)*f/2, hh=(S.yMax-S.yMin)*f/2;
  S.xMin=cx-hw; S.xMax=cx+hw; S.yMin=cy-hh; S.yMax=cy+hh;
  B.zooms++;
  B.lastActivityAt=Date.now();
  render();
}}
function zoomIn()    {{ zoom(0.5); }}
function zoomOut()   {{ zoom(1.6); }}
function resetView() {{
  S.xMin={fxmin}; S.xMax={fxmax}; S.yMin={fymin}; S.yMax={fymax};
  render();
}}
function clearMarkers() {{
  S.markers=[];
  // Reset behavioral counters so fresh data is collected for new attempt
  B.speeds=[]; B.pauseDurations=[]; B.actionIntervals=[]; B.clickTimes=[];
  B.clicks=0; B.zooms=0; B.lastClickTime=null; B.t0=Date.now();
  updateUI(); render();
}}

// ── Mouse move — speed + inactivity tracking ─────────────────────────────────
canvas.addEventListener('mousemove', e => {{
  const now  = Date.now();
  const rect = canvas.getBoundingClientRect();
  const px   = (e.clientX-rect.left)*(canvas.width/rect.width);
  const py   = (e.clientY-rect.top)*(canvas.height/rect.height);
  const fx   = S.xMin+(px/canvas.width)*(S.xMax-S.xMin);
  const fy   = S.yMin+(py/canvas.height)*(S.yMax-S.yMin);
  document.getElementById('coords').textContent = `Re: ${{fx.toFixed(6)}}  Im: ${{fy.toFixed(6)}}`;

  // Speed: pixels moved per millisecond
  if (B.lastMovePos && B.lastMoveTime) {{
    const dx=e.clientX-B.lastMovePos.x, dy=e.clientY-B.lastMovePos.y;
    const dt=now-B.lastMoveTime;
    if (dt>0 && dt<200) {{   // discard huge gaps (tab switches)
      B.speeds.push(parseFloat((Math.sqrt(dx*dx+dy*dy)/dt).toFixed(4)));
      if (B.speeds.length > 200) B.speeds.shift(); // cap rolling window
    }}
  }}
  B.lastMovePos  = {{x:e.clientX, y:e.clientY}};
  B.lastMoveTime = now;
  B.lastActivityAt = now;
}});

// ── Click — inter-click intervals + marker placement ─────────────────────────
canvas.addEventListener('click', e => {{
  const now = Date.now();

  // Record time since last click (inter-click interval)
  if (B.lastClickTime !== null) {{
    B.actionIntervals.push(now - B.lastClickTime);
  }}
  B.lastClickTime  = now;
  B.lastActivityAt = now;
  B.clicks++;
  B.clickTimes.push(now);

  if (S.markers.length >= 3) {{
    setStatus('Max 3 markers. CLEAR to restart.','');
    return;
  }}

  const rect=canvas.getBoundingClientRect();
  const px=(e.clientX-rect.left)*(canvas.width/rect.width);
  const py=(e.clientY-rect.top)*(canvas.height/rect.height);
  const fx=S.xMin+(px/canvas.width)*(S.xMax-S.xMin);
  const fy=S.yMin+(py/canvas.height)*(S.yMax-S.yMin);
  S.markers.push({{fx,fy}});
  updateUI();
  render();

  if (S.markers.length===3) sendToStreamlit();
}});

// ── UI helpers ────────────────────────────────────────────────────────────────
function updateUI() {{
  document.getElementById('mc').textContent=`Markers: ${{S.markers.length}} / 3`;
  document.getElementById('tags').innerHTML=S.markers.map((m,i)=>
    `<span class="tag">P${{i+1}}: (${{m.fx.toFixed(4)}}, ${{m.fy.toFixed(4)}})</span>`
  ).join('');
}}
function setStatus(msg,cls) {{
  const el=document.getElementById('status');
  el.textContent=msg; el.className='status '+cls;
}}

// ── Push data to Streamlit via parent window URL param ────────────────────────
function sendToStreamlit() {{
  const payload = {{
    markers: S.markers,
    behavior: {{
      mouse_speeds:     B.speeds.slice(-80),      // last 80 speed samples
      pause_durations:  B.pauseDurations,         // real inactivity gaps
      click_count:      B.clicks,
      zoom_count:       B.zooms,
      fractal_time_ms:  Date.now() - B.t0,        // total ms on this fractal
      action_intervals: B.actionIntervals,        // inter-click timing
    }}
  }};
  try {{
    const encoded = encodeURIComponent(JSON.stringify(payload));
    const url     = new URL(window.parent.location.href);
    url.searchParams.set('fractal_markers', decodeURIComponent(encoded));
    window.parent.history.replaceState({{}}, '', url);
    setStatus('✓ 3 markers captured — click CONFIRM KEY →','ok');
  }} catch(err) {{
    setStatus('⚠ Frame communication error: ' + err.message,'');
  }}
}}

// ── Init ──────────────────────────────────────────────────────────────────────
render();
updateUI();
if (S.markers.length===3) {{
  sendToStreamlit();
  setStatus('✓ Markers loaded — click CONFIRM KEY →','ok');
}}
</script>
</body></html>"""