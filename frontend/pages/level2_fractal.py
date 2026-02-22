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

    # ── Read markers from query params (set by iframe JS) ────────────────────
    qp = st.query_params
    if "fractal_markers" in qp and not st.session_state.get("fractal_markers"):
        try:
            data = json.loads(qp["fractal_markers"])
            if len(data.get("markers", [])) == 3:
                st.session_state.fractal_markers = data["markers"]
                beh = st.session_state.get("behavior_data", {})
                beh.update(data.get("behavior", {}))
                st.session_state.behavior_data = beh
                qp.clear()
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
        ftype = st.selectbox("FRACTAL TYPE", ["mandelbrot", "julia"],
                             index=0 if fractal_type == "mandelbrot" else 1, key="ftype_sel")
        if ftype != st.session_state.get("fractal_type", "mandelbrot"):
            st.session_state.fractal_type    = ftype
            st.session_state.fractal_markers = []
            st.rerun()
        fractal_type = ftype

    confirmed     = st.session_state.get("fractal_markers", [])
    existing_json = json.dumps(confirmed)

    components.html(_build_fractal_html(fractal_type, mode, existing_json), height=520, scrolling=False)

    if confirmed:
        st.markdown('<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.65rem;color:#00ff88;letter-spacing:2px;margin:8px 0 6px;">✓ MARKERS CAPTURED:</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, (col, m) in enumerate(zip(cols, confirmed)):
            col.markdown(f"""<div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;color:#00ff88;
                padding:8px;border:1px solid rgba(0,255,136,0.3);border-radius:2px;
                background:rgba(0,255,136,0.04);text-align:center;">
                <b>P{i+1}</b><br>Re: {m['fx']:.5f}<br>Im: {m['fy']:.5f}</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="font-family:'Share Tech Mono',monospace;font-size:0.68rem;color:#ff6b35;
            padding:10px;border:1px solid rgba(255,107,53,0.3);border-radius:2px;
            background:rgba(255,107,53,0.04);margin:8px 0;">
            ⚠ Click 3 spots on the fractal above to place your markers.</div>""", unsafe_allow_html=True)

    st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:10px 0;">
      <div style="width:6px;height:6px;border-radius:50%;background:#00ff88;animation:blink 1s infinite;flex-shrink:0;"></div>
      <span style="font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#4a7a9b;">
        BEHAVIORAL METRICS RECORDING — timing, zoom pattern, click precision</span>
    </div><style>@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}</style>""", unsafe_allow_html=True)

    col_back, _, col_next = st.columns([1, 2, 1])
    with col_back:
        if st.button("← BACK", key="l2_back"):
            st.session_state.step            = 1
            st.session_state.fractal_markers = []
            qp.clear()
            st.rerun()
    with col_next:
        if st.button("CONFIRM KEY →", key="l2_next", use_container_width=True):
            if len(confirmed) < 3:
                st.error("Place 3 markers on the fractal first.")
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
            st.error(r.json().get("detail", "Fractal key mismatch"))


def _build_fractal_html(fractal_type: str, mode: str, existing_markers_json: str) -> str:
    fxmin = -2.5 if fractal_type == "mandelbrot" else -1.8
    fxmax =  1.0 if fractal_type == "mandelbrot" else  1.8
    fymin = -1.25 if fractal_type == "mandelbrot" else -1.2
    fymax =  1.25 if fractal_type == "mandelbrot" else  1.2
    init_status = ("Navigate to your registered regions and place your 3 markers."
                   if mode == "login" else "Choose 3 memorable spots and click to mark them.")

    return f"""<!DOCTYPE html><html><head><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#020408;color:#c8e6ff;font-family:'Share Tech Mono',monospace;overflow:hidden;padding:4px;}}
canvas{{display:block;cursor:crosshair;border:1px solid #0a2040;width:100%;}}
.ctrl{{display:flex;gap:6px;padding:6px 0;flex-wrap:wrap;align-items:center;}}
.btn{{padding:6px 14px;background:rgba(0,212,255,0.06);color:#00d4ff;border:1px solid #00d4ff;border-radius:2px;cursor:pointer;font-family:inherit;font-size:0.65rem;letter-spacing:1px;}}
.btn:hover{{background:rgba(0,212,255,0.16);}}
.btn.red{{color:#ff3366;border-color:#ff3366;background:rgba(255,51,102,0.06);}}
.coords{{font-size:0.68rem;color:#00d4ff;padding:5px 10px;background:rgba(0,212,255,0.04);border:1px solid #0a2040;border-radius:2px;margin-top:5px;}}
.tags{{display:flex;flex-wrap:wrap;gap:5px;margin-top:5px;}}
.tag{{font-size:0.62rem;color:#00ff88;padding:2px 7px;border:1px solid rgba(0,255,136,0.3);border-radius:2px;background:rgba(0,255,136,0.05);}}
.status{{font-size:0.63rem;color:#4a7a9b;margin-top:5px;min-height:16px;}}
.status.ok{{color:#00ff88;font-weight:bold;}}
</style></head><body>
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
const canvas=document.getElementById('fc'),ctx=canvas.getContext('2d');
canvas.width=canvas.parentElement?canvas.parentElement.offsetWidth:660;
let S={{type:'{fractal_type}',xMin:{fxmin},xMax:{fxmax},yMin:{fymin},yMax:{fymax},markers:[],busy:false}};
const preloaded={existing_markers_json};
if(Array.isArray(preloaded)&&preloaded.length>0) S.markers=preloaded.map(m=>({{fx:m.fx,fy:m.fy}}));
let B={{speeds:[],pauses:[],clicks:0,zooms:0,lastPos:null,lastTime:null,lastAct:Date.now(),t0:Date.now()}};
function mandelbrot(cx,cy,mi){{let x=0,y=0,i=0;while(x*x+y*y<=4&&i<mi){{const t=x*x-y*y+cx;y=2*x*y+cy;x=t;i++;}}return i;}}
function julia(zx,zy,cx,cy,mi){{let i=0;while(zx*zx+zy*zy<=4&&i<mi){{const t=zx*zx-zy*zy+cx;zy=2*zx*zy+cy;zx=t;i++;}}return i;}}
function colorOf(i,mi){{if(i===mi)return[2,6,15];const t=i/mi;return[Math.min(255,Math.floor(9*(1-t)*t*t*t*255)+10),Math.min(255,Math.floor(15*(1-t)*(1-t)*t*t*255)+40),Math.min(255,Math.floor(8.5*(1-t)**3*t*255)+80)];}}
function render(){{if(S.busy)return;S.busy=true;const W=canvas.width,H=canvas.height,img=ctx.createImageData(W,H),mi=80;for(let py=0;py<H;py++)for(let px=0;px<W;px++){{const cx=S.xMin+(px/W)*(S.xMax-S.xMin),cy=S.yMin+(py/H)*(S.yMax-S.yMin),it=S.type==='mandelbrot'?mandelbrot(cx,cy,mi):julia(cx,cy,-0.7,0.27,mi),[r,g,b]=colorOf(it,mi),idx=(py*W+px)*4;img.data[idx]=r;img.data[idx+1]=g;img.data[idx+2]=b;img.data[idx+3]=255;}}ctx.putImageData(img,0,0);drawMarkers();S.busy=false;}}
function drawMarkers(){{const W=canvas.width,H=canvas.height;S.markers.forEach((m,i)=>{{const px=((m.fx-S.xMin)/(S.xMax-S.xMin))*W,py=((m.fy-S.yMin)/(S.yMax-S.yMin))*H;ctx.beginPath();ctx.arc(px,py,8,0,Math.PI*2);ctx.strokeStyle='#00ff88';ctx.lineWidth=2;ctx.stroke();ctx.beginPath();ctx.moveTo(px-13,py);ctx.lineTo(px+13,py);ctx.moveTo(px,py-13);ctx.lineTo(px,py+13);ctx.strokeStyle='rgba(0,255,136,0.5)';ctx.lineWidth=1;ctx.stroke();ctx.fillStyle='#00ff88';ctx.font='bold 11px monospace';ctx.fillText('P'+(i+1),px+10,py-9);}});}}
function zoom(f){{const cx=(S.xMin+S.xMax)/2,cy=(S.yMin+S.yMax)/2,hw=(S.xMax-S.xMin)*f/2,hh=(S.yMax-S.yMin)*f/2;S.xMin=cx-hw;S.xMax=cx+hw;S.yMin=cy-hh;S.yMax=cy+hh;B.zooms++;render();}}
function zoomIn(){{zoom(0.5);}}function zoomOut(){{zoom(1.6);}}
function resetView(){{S.xMin={fxmin};S.xMax={fxmax};S.yMin={fymin};S.yMax={fymax};render();}}
function clearMarkers(){{S.markers=[];updateUI();render();}}
canvas.addEventListener('mousemove',e=>{{const r=canvas.getBoundingClientRect(),px=(e.clientX-r.left)*(canvas.width/r.width),py=(e.clientY-r.top)*(canvas.height/r.height),fx=S.xMin+(px/canvas.width)*(S.xMax-S.xMin),fy=S.yMin+(py/canvas.height)*(S.yMax-S.yMin);document.getElementById('coords').textContent=`Re: ${{fx.toFixed(6)}}  Im: ${{fy.toFixed(6)}}`;const now=Date.now();if(B.lastPos){{const dx=e.clientX-B.lastPos.x,dy=e.clientY-B.lastPos.y,dt=now-B.lastTime;if(dt>0)B.speeds.push(Math.sqrt(dx*dx+dy*dy)/dt);}}B.lastPos={{x:e.clientX,y:e.clientY}};B.lastTime=now;}});
canvas.addEventListener('click',e=>{{if(S.markers.length>=3){{setStatus('Max 3 markers. CLEAR to restart.','');return;}}const r=canvas.getBoundingClientRect(),px=(e.clientX-r.left)*(canvas.width/r.width),py=(e.clientY-r.top)*(canvas.height/r.height),fx=S.xMin+(px/canvas.width)*(S.xMax-S.xMin),fy=S.yMin+(py/canvas.height)*(S.yMax-S.yMin);S.markers.push({{fx,fy}});B.clicks++;updateUI();render();if(S.markers.length===3)sendToStreamlit();}});
function updateUI(){{document.getElementById('mc').textContent=`Markers: ${{S.markers.length}} / 3`;document.getElementById('tags').innerHTML=S.markers.map((m,i)=>`<span class="tag">P${{i+1}}: (${{m.fx.toFixed(4)}}, ${{m.fy.toFixed(4)}})</span>`).join('');}}
function setStatus(msg,cls){{const el=document.getElementById('status');el.textContent=msg;el.className='status '+cls;}}
function sendToStreamlit(){{
  const payload=encodeURIComponent(JSON.stringify({{
    markers:S.markers,
    behavior:{{mouse_speeds:B.speeds.slice(-60),pause_durations:B.pauses,click_count:B.clicks,zoom_count:B.zooms,fractal_time_ms:Date.now()-B.t0,action_intervals:B.pauses}}
  }}));
  // Update the parent URL query param — Streamlit reads this on next rerun
  const url=new URL(window.parent.location.href);
  url.searchParams.set('fractal_markers', decodeURIComponent(payload));
  window.parent.history.replaceState({{}},'',url);
  setStatus('✓ 3 markers captured — click CONFIRM KEY →','ok');
}}
render();updateUI();
if(S.markers.length===3){{sendToStreamlit();setStatus('✓ Markers loaded — click CONFIRM KEY →','ok');}}
</script></body></html>"""