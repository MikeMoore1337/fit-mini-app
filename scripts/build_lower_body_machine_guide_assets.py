"""Build deterministic YFC-owned SVG key positions for Task 120C exercises."""

from __future__ import annotations

import argparse
from itertools import pairwise
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT_DIR / "backend" / "assets" / "exercise-guides"

SLUG_TO_SCENE = {
    "pendulum-squat": "pendulum_squat",
    "plate-loaded-leg-press": "plate_leg_press",
    "unilateral-leg-press": "unilateral_leg_press",
    "machine-hip-thrust": "hip_thrust",
    "smith-split-squat": "smith_split_squat",
    "machine-glute-kickback": "glute_kickback",
    "v-squat-machine": "v_squat",
    "reverse-hyperextension": "reverse_hyper",
}


def _line(x1: int, y1: int, x2: int, y2: int, kind: str = "body") -> str:
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{kind}" stroke-linecap="round" />'


def _circle(x: int, y: int, radius: int, kind: str = "body-fill") -> str:
    return f'<circle cx="{x}" cy="{y}" r="{radius}" class="{kind}" />'


def _limb(points: tuple[tuple[int, int], ...], kind: str = "body") -> str:
    return "".join(_line(x1, y1, x2, y2, kind) for (x1, y1), (x2, y2) in pairwise(points))


def _plate(x: int, y: int, radius: int = 30) -> str:
    return (
        f'<circle cx="{x}" cy="{y}" r="{radius}" class="weight" />'
        f'<circle cx="{x}" cy="{y}" r="9" class="background" />'
    )


def _weight_stack(x: int, y: int) -> str:
    plates = "".join(
        f'<rect x="{x}" y="{y + offset}" width="58" height="10" rx="3" class="weight" />'
        for offset in range(0, 70, 14)
    )
    return f"<g>{plates}{_line(x + 29, y - 20, x + 29, y + 80, 'cable')}</g>"


def _standing_person(
    *,
    head: tuple[int, int],
    shoulder: tuple[int, int],
    hip: tuple[int, int],
    knee: tuple[int, int],
    foot: tuple[int, int],
) -> str:
    return "".join(
        (
            _circle(*head, 23),
            _line(shoulder[0], shoulder[1], hip[0], hip[1], "torso"),
            _limb((hip, knee, foot)),
            _line(shoulder[0], shoulder[1], shoulder[0] + 55, shoulder[1] + 45),
        )
    )


def _pendulum_squat_scene(active: bool) -> str:
    shoulder = (430, 165) if active else (380, 245)
    hip = (425, 290) if active else (385, 350)
    knee = (465, 360) if active else (485, 380)
    foot = (520, 435)
    frame = (
        _line(85, 450, 660, 450, "frame")
        + _line(105, 445, 135, 75, "frame")
        + _line(135, 75, shoulder[0], shoulder[1], "lever")
        + _line(135, 75, 600, 420, "ghost")
        + _line(470, 440, 635, 440, "platform")
        + _line(shoulder[0] - 35, shoulder[1] - 5, shoulder[0] + 35, shoulder[1] - 5, "pad")
        + _plate(175, 105)
    )
    person = _standing_person(
        head=(shoulder[0] - 5, shoulder[1] - 55),
        shoulder=shoulder,
        hip=hip,
        knee=knee,
        foot=foot,
    )
    return frame + person


def _leg_press_scene(active: bool, *, unilateral: bool) -> str:
    hip = (260, 330)
    shoulder = (215, 205)
    knee = (410, 330) if active else (365, 270)
    foot = (535, 275) if active else (450, 205)
    free_leg = ""
    if unilateral:
        free_leg = _limb((hip, (310, 390), (345, 445)), "ghost-body")
    else:
        free_leg = _limb(
            ((hip[0] + 16, hip[1]), (knee[0] + 12, knee[1] + 15), (foot[0], foot[1] + 18))
        )
    body = (
        _circle(190, 158, 23)
        + _line(shoulder[0], shoulder[1], hip[0], hip[1], "torso")
        + _limb((hip, knee, foot))
        + free_leg
    )
    frame = (
        _line(80, 450, 660, 450, "frame")
        + _line(145, 420, 225, 190, "pad")
        + _line(180, 355, 315, 355, "seat")
        + _line(600, 90, 530, 410, "frame")
        + _line(600, 90, foot[0], foot[1], "lever")
        + _line(550, 135, 650, 165, "platform")
        + _plate(625, 285, 28 if unilateral else 34)
        + (_weight_stack(90, 315) if unilateral else _plate(625, 355, 34))
    )
    return frame + body


def _hip_thrust_scene(active: bool) -> str:
    shoulder = (245, 250)
    hip = (390, 250) if active else (385, 345)
    knee = (500, 330)
    foot = (535, 445)
    pad_y = hip[1] - 10
    person = (
        _circle(195, 220, 23)
        + _line(shoulder[0], shoulder[1], hip[0], hip[1], "torso")
        + _limb((hip, knee, foot))
    )
    machine = (
        _line(75, 450, 660, 450, "frame")
        + _line(145, 285, 290, 285, "pad")
        + _line(180, 285, 130, 450, "frame")
        + _line(620, 430, 610, 95, "frame")
        + _line(610, 95, hip[0], pad_y, "lever")
        + _line(hip[0] - 45, pad_y, hip[0] + 45, pad_y, "pad")
        + _plate(605, 305)
    )
    return machine + person


def _smith_split_squat_scene(active: bool) -> str:
    shoulder = (355, 165) if active else (365, 245)
    hip = (385, 295) if active else (405, 365)
    front_knee = (475, 350) if active else (500, 395)
    front_foot = (565, 445)
    rear_knee = (305, 370) if active else (320, 410)
    rear_foot = (205, 445)
    body = (
        _circle(345, shoulder[1] - 55, 23)
        + _line(shoulder[0], shoulder[1], hip[0], hip[1], "torso")
        + _limb((hip, front_knee, front_foot))
        + _limb((hip, rear_knee, rear_foot), "ghost-body")
        + _line(shoulder[0], shoulder[1], 420, shoulder[1] + 35)
    )
    machine = (
        _line(85, 450, 650, 450, "frame")
        + _line(145, 450, 145, 65, "frame")
        + _line(575, 450, 575, 65, "frame")
        + _line(145, 65, 575, 65, "frame")
        + _line(210, shoulder[1] - 8, 510, shoulder[1] - 8, "bar")
        + _plate(210, shoulder[1] - 8, 25)
        + _plate(510, shoulder[1] - 8, 25)
        + _line(170, 390, 235, 390, "stop")
        + _line(485, 390, 550, 390, "stop")
    )
    return machine + body


def _glute_kickback_scene(active: bool) -> str:
    shoulder = (330, 200)
    hip = (390, 300)
    knee = (505, 315) if active else (425, 390)
    foot = (600, 300) if active else (455, 445)
    body = (
        _circle(285, 160, 23)
        + _line(shoulder[0], shoulder[1], hip[0], hip[1], "torso")
        + _limb((hip, knee, foot))
        + _limb((hip, (350, 390), (335, 445)), "ghost-body")
        + _line(shoulder[0], shoulder[1], 245, 265)
    )
    machine = (
        _line(80, 450, 660, 450, "frame")
        + _line(135, 445, 145, 90, "frame")
        + _line(145, 90, 570, 90, "frame")
        + _line(245, 260, 335, 205, "pad")
        + _line(590, 90, foot[0], foot[1], "lever")
        + _line(foot[0] - 18, foot[1] - 18, foot[0] + 18, foot[1] + 18, "pad")
        + _weight_stack(90, 300)
    )
    return machine + body


def _v_squat_scene(active: bool) -> str:
    shoulder = (365, 165) if active else (420, 245)
    hip = (395, 290) if active else (445, 345)
    knee = (455, 355) if active else (525, 385)
    foot = (560, 440)
    body = _standing_person(
        head=(shoulder[0] - 25, shoulder[1] - 50),
        shoulder=shoulder,
        hip=hip,
        knee=knee,
        foot=foot,
    )
    machine = (
        _line(75, 450, 660, 450, "frame")
        + _line(115, 445, 520, 90, "frame")
        + _line(520, 90, shoulder[0], shoulder[1], "lever")
        + _line(340, 165, 450, 360, "pad")
        + _line(500, 440, 640, 440, "platform")
        + _line(shoulder[0] - 40, shoulder[1] - 8, shoulder[0] + 30, shoulder[1] - 8, "pad")
        + _plate(545, 135)
    )
    return machine + body


def _reverse_hyper_scene(active: bool) -> str:
    shoulder = (280, 235)
    hip = (440, 260)
    knee = (555, 260) if active else (515, 350)
    foot = (635, 260) if active else (535, 445)
    person = (
        _circle(225, 225, 23)
        + _line(shoulder[0], shoulder[1], hip[0], hip[1], "torso")
        + _limb((hip, knee, foot))
        + _line(shoulder[0], shoulder[1], 150, 300)
    )
    machine = (
        _line(75, 450, 660, 450, "frame")
        + _line(120, 275, 465, 275, "pad")
        + _line(155, 275, 125, 450, "frame")
        + _line(425, 275, 485, 450, "frame")
        + _line(475, 275, foot[0], foot[1], "lever")
        + _plate(505, 300)
        + _line(120, 300, 175, 300, "grip-line")
    )
    return machine + person


def _scene(name: str, active: bool) -> str:
    if name == "pendulum_squat":
        return _pendulum_squat_scene(active)
    if name == "plate_leg_press":
        return _leg_press_scene(active, unilateral=False)
    if name == "unilateral_leg_press":
        return _leg_press_scene(active, unilateral=True)
    if name == "hip_thrust":
        return _hip_thrust_scene(active)
    if name == "smith_split_squat":
        return _smith_split_squat_scene(active)
    if name == "glute_kickback":
        return _glute_kickback_scene(active)
    if name == "v_squat":
        return _v_squat_scene(active)
    if name == "reverse_hyper":
        return _reverse_hyper_scene(active)
    raise ValueError(f"Unknown scene: {name}")


def render_svg(scene: str, *, active: bool) -> str:
    position = "2" if active else "1"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="520" viewBox="0 0 720 520" role="img">
  <style>
    .background {{ fill: #111416; }}
    .frame {{ stroke: #879096; stroke-width: 15; fill: none; }}
    .lever {{ stroke: #b8c0c4; stroke-width: 13; fill: none; }}
    .bar {{ stroke: #d1d7da; stroke-width: 10; fill: none; }}
    .stop {{ stroke: #6f787d; stroke-width: 10; fill: none; }}
    .ghost {{ stroke: #5c666b; stroke-width: 6; stroke-dasharray: 10 12; fill: none; }}
    .cable {{ stroke: #b8c0c4; stroke-width: 4; fill: none; }}
    .pad {{ stroke: #3b454a; stroke-width: 24; fill: none; }}
    .seat {{ stroke: #3b454a; stroke-width: 28; fill: none; }}
    .platform {{ stroke: #6f787d; stroke-width: 18; fill: none; }}
    .weight {{ stroke: #6f787d; stroke-width: 11; fill: #242a2d; }}
    .body {{ stroke: #f2f5f3; stroke-width: 17; fill: none; }}
    .ghost-body {{ stroke: #aab2b6; stroke-width: 14; fill: none; }}
    .torso {{ stroke: #f2f5f3; stroke-width: 34; fill: none; }}
    .body-fill {{ fill: #f2f5f3; }}
    .grip {{ fill: #c8ff2e; }}
    .grip-line {{ stroke: #c8ff2e; stroke-width: 10; fill: none; }}
  </style>
  <rect width="720" height="520" rx="32" class="background" />
  <circle cx="660" cy="55" r="28" fill="#c8ff2e" />
  <text x="660" y="64" text-anchor="middle" font-family="Arial, sans-serif" font-size="26" font-weight="700" fill="#111416">{position}</text>
  {_scene(scene, active)}
</svg>
"""


def build_assets(asset_dir: Path, *, check: bool) -> None:
    stale: list[str] = []
    for slug, scene in SLUG_TO_SCENE.items():
        for suffix, active in (("start", False), ("active", True)):
            path = asset_dir / f"{slug}-{suffix}.svg"
            rendered = render_svg(scene, active=active)
            if check:
                if not path.exists() or path.read_text(encoding="utf-8") != rendered:
                    stale.append(path.name)
            else:
                path.write_text(rendered, encoding="utf-8", newline="\n")
    if stale:
        raise SystemExit("Stale Task 120C guide assets: " + ", ".join(stale))
    print(
        f"Validated {len(SLUG_TO_SCENE) * 2} SVG assets"
        if check
        else f"Wrote {len(SLUG_TO_SCENE) * 2} SVG assets"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-dir", type=Path, default=ASSET_DIR)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    build_assets(args.asset_dir, check=args.check)


if __name__ == "__main__":
    main()
