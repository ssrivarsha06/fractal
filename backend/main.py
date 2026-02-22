"""
FractalAuth Backend — FastAPI
All Level 3 (Behavioral) and Level 4 (Contextual) risk logic lives here.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json, math, statistics, time
from datetime import datetime
import db

app = FastAPI(title="FractalAuth API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRACTAL_THRESHOLD = 0.08  # lenient coordinate matching tolerance

# ─────────────────────────── SCHEMAS ────────────────────────────────────────

class RegisterL1(BaseModel):
    username: str
    email: str
    password: str

class FractalMarker(BaseModel):
    fx: float
    fy: float

class RegisterL2(BaseModel):
    username: str
    fractal_type: str
    markers: List[FractalMarker]

class BehaviorPayload(BaseModel):
    username: str
    mouse_speeds: List[float] = []
    pause_durations: List[float] = []
    click_count: int = 3
    zoom_count: int = 1
    fractal_time_ms: float = 5000.0
    action_intervals: List[float] = []

class RegisterPuzzles(BaseModel):
    username: str
    easy_puzzle: dict
    hard_puzzle: dict

class RegisterBehavior(BaseModel):
    username: str
    mouse_speeds: List[float] = []
    pause_durations: List[float] = []
    click_count: int = 3
    zoom_count: int = 1
    fractal_time_ms: float = 5000.0
    action_intervals: List[float] = []

class LoginL1(BaseModel):
    username: str
    password: str

class LoginL2(BaseModel):
    username: str
    markers: List[FractalMarker]

class RiskRequest(BaseModel):
    username: str
    behavior: BehaviorPayload
    ip_address: Optional[str] = "127.0.0.1"
    user_agent: Optional[str] = ""
    login_hour: Optional[int] = None

class PuzzleVerify(BaseModel):
    username: str
    answer: str

# ─────────────────────────── HELPERS ────────────────────────────────────────

def markers_match(stored: list, incoming: List[FractalMarker]) -> bool:
    if len(stored) != len(incoming):
        return False
    for s, inp in zip(stored, incoming):
        dist = math.sqrt((s["fx"] - inp.fx) ** 2 + (s["fy"] - inp.fy) ** 2)
        if dist > FRACTAL_THRESHOLD:
            return False
    return True


def behavioral_risk(stored_profile: dict, current: BehaviorPayload) -> dict:
    """Level 3 — compare live session behaviour vs registration baseline."""
    logs, scores = [], []

    def deviation_risk(cur, ref, weight, label):
        if ref and ref > 0:
            dev = abs(cur - ref) / (ref + 1e-9)
            risk = min(100, dev * 100)
            scores.append(risk * weight)
            lvl = "WARN" if risk > 40 else "OK"
            logs.append({"level": lvl,
                         "msg": f"{label}: deviation {risk:.1f}%  (now={cur:.3f} | reg={ref:.3f})"})
        else:
            scores.append(10 * weight)
            logs.append({"level": "INFO", "msg": f"{label}: no baseline — assuming low risk"})

    cur_speed  = statistics.mean(current.mouse_speeds)  if current.mouse_speeds  else 0
    cur_pause  = statistics.mean(current.pause_durations) if current.pause_durations else 1000

    deviation_risk(cur_speed, stored_profile.get("avg_mouse_speed", 0),  0.25, "Mouse speed")
    deviation_risk(cur_pause, stored_profile.get("avg_pause_ms", 0),     0.25, "Pause duration")
    deviation_risk(current.fractal_time_ms, stored_profile.get("fractal_time_ms", 0), 0.30, "Fractal time")
    deviation_risk(current.click_count,     stored_profile.get("click_count", 0),     0.20, "Click count")

    return {"risk": min(100, round(sum(scores))), "logs": logs}


def contextual_risk(username: str, ip: str, ua: str, hour: int) -> dict:
    """Level 4 — check device, time, IP, failed attempts."""
    user = db.get_user(username)
    logs, scores = [], []

    # 1. Unusual login hour
    if hour < 5 or hour >= 23:
        scores.append(20)
        logs.append({"level": "WARN", "msg": f"Login at unusual hour: {hour:02d}:xx"})
    else:
        scores.append(0)
        logs.append({"level": "OK",   "msg": f"Login hour {hour:02d}:xx within normal range"})

    # 2. Previous failed attempts
    failed = user.get("failed_attempts", 0)
    if failed >= 3:
        scores.append(35)
        logs.append({"level": "RISK", "msg": f"{failed} previous failed login attempts"})
    elif failed >= 1:
        scores.append(15)
        logs.append({"level": "WARN", "msg": f"{failed} previous failed attempt(s)"})
    else:
        scores.append(0)
        logs.append({"level": "OK",   "msg": "No prior failed attempts"})

    # 3. User-Agent (device) fingerprint
    stored_ua = user.get("registered_ua", "")
    if stored_ua and ua and stored_ua != ua:
        scores.append(20)
        logs.append({"level": "WARN", "msg": "Device/browser fingerprint changed"})
    elif not stored_ua:
        scores.append(5)
        logs.append({"level": "INFO", "msg": "No prior device fingerprint on record"})
    else:
        scores.append(0)
        logs.append({"level": "OK",   "msg": "Device fingerprint consistent"})

    # 4. IP address
    stored_ip = user.get("registered_ip", "")
    if stored_ip and ip and stored_ip != ip:
        scores.append(15)
        logs.append({"level": "WARN", "msg": f"IP changed: {stored_ip} → {ip}"})
    else:
        scores.append(0)
        logs.append({"level": "OK",   "msg": f"IP address consistent ({ip})"})

    # 5. Simulated geo (subnet prefix)
    if stored_ip and ip:
        if stored_ip.rsplit(".", 1)[0] != ip.rsplit(".", 1)[0]:
            scores.append(10)
            logs.append({"level": "WARN", "msg": "Geographic region anomaly detected"})
        else:
            scores.append(0)
            logs.append({"level": "OK",   "msg": "Geographic region consistent"})

    return {"risk": min(100, round(sum(scores))), "logs": logs}

# ─────────────────────────── ROUTES ─────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "FractalAuth API v2 running", "db": "SQLite"}


# ── REGISTRATION ─────────────────────────────────────────────────────────────

@app.post("/register/level1")
def register_l1(data: RegisterL1, request: Request):
    if db.user_exists(data.username):
        raise HTTPException(400, "Username already taken")
    if len(data.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    ip = request.headers.get("x-forwarded-for", "") or (request.client.host if request.client else "")
    ua = request.headers.get("user-agent", "")
    db.create_user(data.username, data.email, data.password, ip, ua)
    return {"success": True, "message": "Identity verified"}


@app.post("/register/level2")
def register_l2(data: RegisterL2):
    if not db.user_exists(data.username):
        raise HTTPException(404, "User not found")
    if len(data.markers) < 3:
        raise HTTPException(400, "Exactly 3 markers required")
    db.update_many(data.username, {
        "fractal_type": data.fractal_type,
        "fractal_markers": [{"fx": m.fx, "fy": m.fy} for m in data.markers],
    })
    return {"success": True}


@app.post("/register/behavior")
def register_behavior(data: RegisterBehavior):
    if not db.user_exists(data.username):
        raise HTTPException(404, "User not found")
    profile = {
        "avg_mouse_speed": statistics.mean(data.mouse_speeds) if data.mouse_speeds else 0,
        "avg_pause_ms":    statistics.mean(data.pause_durations) if data.pause_durations else 1000,
        "fractal_time_ms": data.fractal_time_ms,
        "click_count":     data.click_count,
        "zoom_count":      data.zoom_count,
    }
    db.update_field(data.username, "behavior_profile", profile)
    return {"success": True, "profile": profile}


@app.post("/register/puzzles")
def register_puzzles(data: RegisterPuzzles):
    if not db.user_exists(data.username):
        raise HTTPException(404, "User not found")
    db.update_many(data.username, {
        "easy_puzzle": data.easy_puzzle,
        "hard_puzzle": data.hard_puzzle,
        "is_complete":  1,
    })
    return {"success": True, "message": "Registration complete"}


# ── LOGIN ─────────────────────────────────────────────────────────────────────

@app.post("/login/level1")
def login_l1(data: LoginL1):
    user = db.get_user(data.username)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    if not user.get("is_complete"):
        raise HTTPException(401, "Registration not complete. Please finish registration first.")
    if user["password_hash"] != db.hash_password(data.password):
        db.increment_failed(data.username)
        raise HTTPException(401, "Invalid credentials")
    # Return ONLY fractal type — never coordinates
    return {"success": True, "fractal_type": user["fractal_type"]}


@app.post("/login/level2")
def login_l2(data: LoginL2):
    user = db.get_user(data.username)
    if not user:
        raise HTTPException(404, "User not found")
    if not markers_match(user["fractal_markers"], data.markers):
        db.increment_failed(data.username)
        raise HTTPException(401, "Fractal key mismatch — check your marker positions")
    return {"success": True, "message": "Fractal key verified"}


@app.post("/login/risk-assessment")
def risk_assessment(data: RiskRequest, request: Request):
    """Level 3 + Level 4 combined — returns composite risk + puzzle (answer redacted)."""
    user = db.get_user(data.username)
    if not user:
        raise HTTPException(404, "User not found")

    ip   = data.ip_address or request.headers.get("x-forwarded-for", "127.0.0.1")
    ua   = data.user_agent  or request.headers.get("user-agent", "")
    hour = data.login_hour if data.login_hour is not None else datetime.now().hour

    beh_result = behavioral_risk(user.get("behavior_profile", {}), data.behavior)
    ctx_result = contextual_risk(data.username, ip, ua, hour)

    composite  = round(beh_result["risk"] * 0.5 + ctx_result["risk"] * 0.5)
    difficulty = "hard" if composite >= 40 else "easy"
    raw_puzzle = user["hard_puzzle"] if difficulty == "hard" else user["easy_puzzle"]

    # Strip answer before sending to client
    safe_puzzle = {k: v for k, v in raw_puzzle.items() if k != "answer"}

    return {
        "behavioral_risk":  beh_result["risk"],
        "contextual_risk":  ctx_result["risk"],
        "composite_risk":   composite,
        "risk_level":       "HIGH" if composite >= 60 else "MEDIUM" if composite >= 30 else "LOW",
        "difficulty":       difficulty,
        "puzzle":           safe_puzzle,
        "behavioral_logs":  beh_result["logs"],
        "contextual_logs":  ctx_result["logs"],
    }


@app.post("/login/verify-puzzle")
def verify_puzzle(data: PuzzleVerify):
    user = db.get_user(data.username)
    if not user:
        raise HTTPException(404, "User not found")
    easy_ans = user.get("easy_puzzle", {}).get("answer", "")
    hard_ans = user.get("hard_puzzle", {}).get("answer", "")
    if data.answer in (easy_ans, hard_ans):
        db.reset_failed(data.username)
        return {"success": True, "message": "Authentication complete"}
    db.increment_failed(data.username)
    raise HTTPException(401, "Incorrect answer")


@app.delete("/dev/user/{username}")
def dev_delete_user(username: str):
    db.delete_user(username)
    return {"deleted": username}
