"""
puzzle_gen.py — Generate easy + hard puzzles from fractal marker coordinates.
"""
import math, random


def generate_puzzles(markers: list) -> tuple[dict, dict]:
    return _easy(markers), _hard(markers)


def _easy(markers: list) -> dict:
    m   = markers[0]
    fx  = m["fx"]
    ans = f"Re: {fx:.3f}"
    others = []
    for delta in [0.25, -0.3, 0.55, -0.6]:
        opt = f"Re: {fx + delta:.3f}"
        if opt != ans:
            others.append(opt)
    options = ([ans] + others[:3])
    random.shuffle(options)
    return {
        "question":     "Which real coordinate is closest to your registered marker P1?",
        "options":      options,
        "answer":       ans,
        "fractal_hint": f"Hint: Your P1 was near Re ≈ {fx:.2f}",
    }


def _hard(markers: list) -> dict:
    m1 = markers[0]
    m2 = markers[1] if len(markers) > 1 else markers[0]

    q_type = random.randint(0, 2)

    if q_type == 0:
        val = math.floor(abs(m1["fx"])) + math.floor(abs(m1["fy"]))
        ans = str(val)
        q   = "What is ⌊|P1.Re|⌋ + ⌊|P1.Im|⌋ for your registered first marker?"
        hint = "Take the floor of the absolute value of each coordinate and add them."
    elif q_type == 1:
        neg = sum(1 for m in markers if m["fx"] < 0)
        ans = str(neg)
        q   = "How many of your 3 registered markers have a NEGATIVE real (Re) coordinate?"
        hint = "Consider which side of the imaginary axis each marker was placed on."
    else:
        val = round(m1["fx"])
        ans = str(val)
        q   = "What is your P1 real coordinate rounded to the nearest integer?"
        hint = f"Your P1 real value is close to {m1['fx']:.1f}"

    base = int(ans)
    wrongs = list({str(base+1), str(base-1), str(base+2), str(base-2)} - {ans})[:3]
    options = [ans] + wrongs
    random.shuffle(options)

    return {"question": q, "options": options, "answer": ans, "fractal_hint": hint}
