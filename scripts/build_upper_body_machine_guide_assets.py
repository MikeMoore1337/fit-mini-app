"""Build deterministic YFC-owned SVG key positions for Task 120B exercises."""

from __future__ import annotations

import argparse
from itertools import pairwise
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT_DIR / "backend" / "assets" / "exercise-guides"

SLUG_TO_SCENE = {
    "machine-incline-chest-press": "incline_press",
    "independent-lever-chest-press": "chest_press",
    "lever-high-row": "high_row",
    "lever-low-row": "low_row",
    "independent-lever-lat-pulldown": "lat_pulldown",
    "machine-pullover": "pullover",
    "independent-lever-shoulder-press": "shoulder_press",
    "machine-decline-chest-press": "decline_press",
    "machine-triceps-extension": "triceps_extension",
    "chest-supported-dumbbell-row": "dumbbell_row",
}


def _line(x1: int, y1: int, x2: int, y2: int, kind: str = "body") -> str:
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{kind}" stroke-linecap="round" />'


def _circle(x: int, y: int, radius: int, kind: str = "body-fill") -> str:
    return f'<circle cx="{x}" cy="{y}" r="{radius}" class="{kind}" />'


def _limb(points: tuple[tuple[int, int], ...], kind: str = "body") -> str:
    return "".join(_line(x1, y1, x2, y2, kind) for (x1, y1), (x2, y2) in pairwise(points))


def _weight_stack(x: int, y: int) -> str:
    plates = "".join(
        f'<rect x="{x}" y="{y + offset}" width="58" height="10" rx="3" class="weight" />'
        for offset in range(0, 70, 14)
    )
    return f"<g>{plates}{_line(x + 29, y - 20, x + 29, y + 80, 'cable')}</g>"


def _plate(x: int, y: int) -> str:
    return (
        f'<circle cx="{x}" cy="{y}" r="34" class="weight" />'
        f'<circle cx="{x}" cy="{y}" r="10" class="background" />'
    )


def _seated_person(
    *,
    shoulder: tuple[int, int],
    elbow: tuple[int, int],
    hand: tuple[int, int],
    facing: str = "right",
) -> str:
    sx, sy = shoulder
    direction = 1 if facing == "right" else -1
    head_x = sx + 2 * direction
    head_y = sy - 48
    hip = (sx, sy + 132)
    knee = (sx + 78 * direction, sy + 170)
    foot = (sx + 110 * direction, sy + 238)
    return "".join(
        (
            _circle(head_x, head_y, 24),
            _line(sx, sy - 18, hip[0], hip[1], "torso"),
            _limb((shoulder, elbow, hand)),
            _limb((hip, knee, foot)),
            _circle(hand[0], hand[1], 8, "grip"),
        )
    )


def _press_scene(kind: str, active: bool) -> str:
    shoulder = (350, 205)
    if kind == "incline_press":
        elbow = (432, 205) if active else (395, 248)
        hand = (555, 128) if active else (455, 225)
        track_end = (565, 118)
        stack = _weight_stack(590, 260)
        back = _line(320, 180, 350, 350, "pad")
    elif kind == "decline_press":
        elbow = (448, 258) if active else (400, 245)
        hand = (570, 302) if active else (455, 248)
        track_end = (580, 312)
        stack = _weight_stack(590, 120)
        back = _line(318, 175, 355, 350, "pad")
    else:
        elbow = (465, 215) if active else (400, 250)
        hand = (580, 215) if active else (460, 238)
        track_end = (590, 215)
        stack = _plate(610, 150) + _plate(610, 285)
        back = _line(318, 175, 340, 350, "pad")
    lever = _line(620, 105, hand[0], hand[1], "lever") + _line(
        620, 105, track_end[0], track_end[1], "ghost"
    )
    frame = (
        _line(115, 445, 650, 445, "frame")
        + _line(120, 445, 170, 90, "frame")
        + _line(650, 445, 620, 105, "frame")
        + _line(170, 90, 620, 105, "frame")
        + _line(300, 350, 455, 350, "seat")
        + back
        + stack
        + lever
    )
    return frame + _seated_person(shoulder=shoulder, elbow=elbow, hand=hand)


def _row_scene(kind: str, active: bool) -> str:
    shoulder = (375, 205)
    if kind == "high_row":
        elbow = (440, 245) if active else (270, 155)
        hand = (295, 230) if active else (170, 125)
        pivot = (115, 80)
    else:
        elbow = (445, 278) if active else (270, 325)
        hand = (305, 300) if active else (165, 350)
        pivot = (105, 405)
    frame = (
        _line(90, 445, 650, 445, "frame")
        + _line(105, 445, pivot[0], pivot[1], "frame")
        + _line(pivot[0], pivot[1], hand[0], hand[1], "lever")
        + _line(650, 445, 610, 95, "frame")
        + _plate(120, 245)
        + _line(330, 175, 350, 330, "pad")
        + _line(300, 350, 450, 350, "seat")
    )
    return frame + _seated_person(
        shoulder=shoulder,
        elbow=elbow,
        hand=hand,
        facing="left",
    )


def _lat_pulldown_scene(active: bool) -> str:
    shoulder_left, shoulder_right = (330, 205), (390, 205)
    if active:
        elbows = ((285, 250), (435, 250))
        hands = ((320, 205), (400, 205))
    else:
        elbows = ((300, 135), (420, 135))
        hands = ((275, 80), (445, 80))
    arms = (
        _limb((shoulder_left, elbows[0], hands[0]))
        + _limb((shoulder_right, elbows[1], hands[1]))
        + _circle(hands[0][0], hands[0][1], 8, "grip")
        + _circle(hands[1][0], hands[1][1], 8, "grip")
    )
    body = (
        _circle(360, 155, 24)
        + _line(360, 180, 360, 335, "torso")
        + arms
        + _limb(((360, 335), (310, 375), (295, 445)))
        + _limb(((360, 335), (410, 375), (425, 445)))
    )
    machine = (
        _line(85, 445, 635, 445, "frame")
        + _line(110, 445, 135, 70, "frame")
        + _line(610, 445, 585, 70, "frame")
        + _line(135, 70, 585, 70, "frame")
        + _line(135, 70, hands[0][0], hands[0][1], "lever")
        + _line(585, 70, hands[1][0], hands[1][1], "lever")
        + _plate(120, 230)
        + _plate(600, 230)
        + _line(290, 335, 430, 335, "seat")
        + _line(285, 310, 435, 310, "pad")
    )
    return machine + body


def _pullover_scene(active: bool) -> str:
    shoulder = (365, 205)
    elbow = (320, 235) if active else (325, 125)
    hand = (245, 315) if active else (285, 75)
    machine = (
        _line(90, 445, 650, 445, "frame")
        + _line(620, 445, 610, 75, "frame")
        + _line(610, 75, hand[0], hand[1], "lever")
        + _weight_stack(555, 280)
        + _line(320, 175, 350, 350, "pad")
        + _line(300, 350, 455, 350, "seat")
        + _line(elbow[0] - 26, elbow[1], elbow[0] + 26, elbow[1], "pad")
    )
    return machine + _seated_person(
        shoulder=shoulder,
        elbow=elbow,
        hand=hand,
        facing="left",
    )


def _shoulder_press_scene(active: bool) -> str:
    shoulder = (360, 205)
    elbow = (405, 125) if active else (410, 255)
    hand = (420, 70) if active else (440, 190)
    machine = (
        _line(90, 445, 650, 445, "frame")
        + _line(110, 445, 140, 85, "frame")
        + _line(640, 445, 610, 85, "frame")
        + _line(140, 85, 610, 85, "frame")
        + _line(600, 95, hand[0], hand[1], "lever")
        + _plate(610, 270)
        + _line(315, 175, 340, 350, "pad")
        + _line(300, 350, 455, 350, "seat")
    )
    return machine + _seated_person(shoulder=shoulder, elbow=elbow, hand=hand)


def _triceps_scene(active: bool) -> str:
    shoulder = (345, 205)
    elbow = (405, 225)
    hand = (520, 275) if active else (450, 145)
    machine = (
        _line(90, 445, 650, 445, "frame")
        + _line(600, 445, 585, 105, "frame")
        + _line(585, 105, hand[0], hand[1], "lever")
        + _weight_stack(535, 285)
        + _line(320, 175, 340, 350, "pad")
        + _line(300, 350, 455, 350, "seat")
        + _line(375, 240, 455, 240, "pad")
    )
    return machine + _seated_person(shoulder=shoulder, elbow=elbow, hand=hand)


def _dumbbell_row_scene(active: bool) -> str:
    shoulder = (385, 205)
    hip = (510, 300)
    elbow = (500, 245) if active else (405, 305)
    hand = (445, 300) if active else (395, 395)
    person = (
        _circle(345, 165, 24)
        + _line(365, 190, hip[0], hip[1], "torso")
        + _limb((shoulder, elbow, hand))
        + _limb((hip, (565, 350), (610, 445)))
        + _line(hand[0] - 22, hand[1], hand[0] + 22, hand[1], "weight")
    )
    bench = (
        _line(100, 445, 650, 445, "frame")
        + _line(260, 390, 520, 255, "pad")
        + _line(320, 360, 290, 445, "frame")
        + _line(480, 275, 540, 445, "frame")
    )
    return bench + person


def _scene(name: str, active: bool) -> str:
    if name in {"incline_press", "chest_press", "decline_press"}:
        return _press_scene(name, active)
    if name in {"high_row", "low_row"}:
        return _row_scene(name, active)
    if name == "lat_pulldown":
        return _lat_pulldown_scene(active)
    if name == "pullover":
        return _pullover_scene(active)
    if name == "shoulder_press":
        return _shoulder_press_scene(active)
    if name == "triceps_extension":
        return _triceps_scene(active)
    if name == "dumbbell_row":
        return _dumbbell_row_scene(active)
    raise ValueError(f"Unknown scene: {name}")


def render_svg(scene: str, *, active: bool) -> str:
    position = "2" if active else "1"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="520" viewBox="0 0 720 520" role="img">
  <style>
    .background {{ fill: #111416; }}
    .frame {{ stroke: #879096; stroke-width: 15; fill: none; }}
    .lever {{ stroke: #b8c0c4; stroke-width: 13; fill: none; }}
    .ghost {{ stroke: #5c666b; stroke-width: 6; stroke-dasharray: 10 12; fill: none; }}
    .cable {{ stroke: #b8c0c4; stroke-width: 4; fill: none; }}
    .pad {{ stroke: #3b454a; stroke-width: 24; fill: none; }}
    .seat {{ stroke: #3b454a; stroke-width: 28; fill: none; }}
    .weight {{ stroke: #6f787d; stroke-width: 11; fill: #242a2d; }}
    .body {{ stroke: #f2f5f3; stroke-width: 17; fill: none; }}
    .torso {{ stroke: #f2f5f3; stroke-width: 34; fill: none; }}
    .body-fill {{ fill: #f2f5f3; }}
    .grip {{ fill: #c8ff2e; }}
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
                path.write_text(rendered, encoding="utf-8")
    if stale:
        raise SystemExit("Stale Task 120B guide assets: " + ", ".join(stale))
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
