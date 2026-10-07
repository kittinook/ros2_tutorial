"""Draws the world with pygame: the map on the left, the mission panel on the right."""

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

import pygame

from mars_sim import world as W

MAP_PX = 680                     # the map is MAP_PX x MAP_PX pixels
PANEL_PX = 320
SCALE = MAP_PX / W.WORLD_SIZE    # pixels per metre

GROUND = (193, 112, 64)
GROUND_DARK = (170, 94, 52)
GROUND_LIGHT = (208, 132, 82)
SAND = (222, 168, 104)
SAND_RIPPLE = (200, 145, 86)
CRATER_FLOOR = (160, 86, 48)
CRATER_RIM = (216, 142, 92)
ROCK = (96, 66, 52)
ROCK_LIGHT = (134, 98, 80)
ROCK_EDGE = (54, 36, 28)
SAMPLE = (70, 205, 215)
LANDER_PAD = (110, 112, 120)
LANDER_BODY = (214, 218, 222)
AMBER = (242, 165, 65)
FLAG = (40, 120, 235)
ROVER_BODY = (238, 238, 232)
ROVER_DECK = (52, 82, 132)
WHEEL = (36, 36, 40)
PANEL = (19, 41, 61)
PANEL_TEXT = (226, 232, 228)
PANEL_DIM = (143, 163, 176)
GREEN = (120, 210, 140)
RED = (240, 110, 90)
CYAN = (130, 200, 230)


# the part of the map on screen: bottom-left corner (metres) and pixels per metre (set_view zooms in)
VIEW = {'x0': 0.0, 'y0': 0.0, 'scale': SCALE}


def set_view(zoom: float, cx: float, cy: float):
    zoom = max(1.0, zoom)
    size = W.WORLD_SIZE / zoom
    VIEW['x0'] = min(max(cx - size / 2, 0.0), W.WORLD_SIZE - size)
    VIEW['y0'] = min(max(cy - size / 2, 0.0), W.WORLD_SIZE - size)
    VIEW['scale'] = MAP_PX / size


def to_px(x: float, y: float) -> Tuple[int, int]:
    return (int(round((x - VIEW['x0']) * VIEW['scale'])),
            int(round(MAP_PX - (y - VIEW['y0']) * VIEW['scale'])))


def px(length: float) -> int:
    return max(1, int(round(length * VIEW['scale'])))


class Renderer:
    def __init__(self, headless: bool = False):
        pygame.init()
        pygame.display.set_caption('Mars Rover Academy')
        self.screen = pygame.display.set_mode((MAP_PX + PANEL_PX, MAP_PX))
        self.font = self._font(15)
        self.font_small = self._font(13)
        self.font_bold = self._font(17, bold=True)
        self.font_title = self._font(20, bold=True)
        self.font_mono = self._font(13, mono=True)
        self.ground: Optional[pygame.Surface] = None
        self.ground_version = -1

    @staticmethod
    def _font(size: int, bold: bool = False, mono: bool = False) -> pygame.font.Font:
        names = 'dejavusansmono,liberationmono,monospace' if mono else 'dejavusans,liberationsans,arial'
        return pygame.font.SysFont(names, size, bold=bold)

    # ------------------------------------------------------------------ the ground (redrawn only when it changes)
    def _draw_ground(self, world: W.World, show_grid: bool):
        g = pygame.Surface((MAP_PX, MAP_PX))
        g.fill(GROUND)
        rng = random.Random(7)
        for _ in range(2500):                       # dust and pebbles
            x, y = rng.randrange(MAP_PX), rng.randrange(MAP_PX)
            colour = GROUND_DARK if rng.random() < 0.6 else GROUND_LIGHT
            pygame.draw.circle(g, colour, (x, y), rng.choice((1, 1, 1, 2)))

        for o in world.of_kind('sand'):
            c, r = to_px(o.x, o.y), px(o.radius)
            pygame.draw.circle(g, SAND, c, r)
            ripples = random.Random(o.id)
            for k in range(-r + 6, r - 4, 7):       # dune ripples
                half = math.sqrt(max(r * r - k * k, 0)) * 0.85
                wobble = ripples.uniform(-3, 3)
                pygame.draw.arc(g, SAND_RIPPLE, (c[0] - half, c[1] + k - 4 + wobble, 2 * half, 10), 0.3, math.pi - 0.3, 1)
        for o in world.of_kind('crater'):
            c, r = to_px(o.x, o.y), px(o.radius)
            pygame.draw.circle(g, CRATER_RIM, c, r + 4)
            pygame.draw.circle(g, CRATER_FLOOR, c, r)
            pygame.draw.circle(g, GROUND_DARK, (c[0] - r // 5, c[1] - r // 5), int(r * 0.75))
            pygame.draw.circle(g, CRATER_FLOOR, (c[0] + r // 8, c[1] + r // 8), int(r * 0.7))

        # the lander pad
        c, r = to_px(*W.LANDER), px(W.LANDER_RADIUS)
        pygame.draw.circle(g, LANDER_PAD, c, r)
        for a in range(0, 360, 20):                 # dashed yellow ring
            pygame.draw.arc(g, AMBER, (c[0] - r, c[1] - r, 2 * r, 2 * r), math.radians(a), math.radians(a + 10), 3)

        if show_grid:
            overlay = pygame.Surface((MAP_PX, MAP_PX), pygame.SRCALPHA)
            for m in range(1, int(W.WORLD_SIZE)):
                alpha = 55 if m % 5 == 0 or VIEW['scale'] > 60 else 22
                x, _ = to_px(m, 0)
                _, y = to_px(0, m)
                pygame.draw.line(overlay, (255, 255, 255, alpha), (x, 0), (x, MAP_PX))
                pygame.draw.line(overlay, (255, 255, 255, alpha), (0, y), (MAP_PX, y))
            g.blit(overlay, (0, 0))
            step = 1 if VIEW['scale'] > 60 else 2
            for m in range(step, int(W.WORLD_SIZE), step):
                x, _ = to_px(m, 0)
                _, y = to_px(0, m)
                self._text(g, str(m), self.font_small, (255, 240, 225), (x, MAP_PX - 9), anchor='center', shadow=True)
                self._text(g, str(m), self.font_small, (255, 240, 225), (9, y), anchor='center', shadow=True)
        self.ground = g

    # ------------------------------------------------------------------ helpers
    def _text(self, surf, text, font, colour, pos, anchor='topleft', shadow=False):
        if shadow:
            s = font.render(text, True, (40, 20, 10))
            rect = s.get_rect(**{anchor: (pos[0] + 1, pos[1] + 1)})
            surf.blit(s, rect)
        s = font.render(text, True, colour)
        rect = s.get_rect(**{anchor: pos})
        surf.blit(s, rect)
        return rect

    @staticmethod
    def _rotated(points, x, y, yaw):
        c, s = math.cos(yaw), math.sin(yaw)
        return [to_px(x + c * px_ - s * py_, y + s * px_ + c * py_) for px_, py_ in points]

    def _rock(self, surf, o: W.WorldObject):
        rng = random.Random(o.id)
        pts = []
        for k in range(9):
            a = 2 * math.pi * k / 9 + rng.uniform(-0.2, 0.2)
            rr = o.radius * rng.uniform(0.82, 1.05)
            pts.append((o.x + rr * math.cos(a), o.y + rr * math.sin(a)))
        poly = [to_px(*p) for p in pts]
        shadow = [(p[0] + 4, p[1] + 4) for p in poly]
        pygame.draw.polygon(surf, (120, 62, 34), shadow)
        pygame.draw.polygon(surf, ROCK, poly)
        cx, cy = to_px(o.x - o.radius * 0.25, o.y + o.radius * 0.25)
        pygame.draw.circle(surf, ROCK_LIGHT, (cx, cy), max(2, px(o.radius * 0.4)))
        pygame.draw.polygon(surf, ROCK_EDGE, poly, 2)

    def _flag(self, surf, x, y, radius, label):
        c = to_px(x, y)
        ring = pygame.Surface((2 * px(radius) + 4, 2 * px(radius) + 4), pygame.SRCALPHA)
        rc = (px(radius) + 2, px(radius) + 2)
        pygame.draw.circle(ring, (255, 255, 255, 50), rc, px(radius))
        pygame.draw.circle(ring, (255, 255, 255, 170), rc, px(radius), 2)
        surf.blit(ring, (c[0] - rc[0], c[1] - rc[1]))
        pygame.draw.line(surf, (40, 40, 40), c, (c[0], c[1] - 26), 3)
        pygame.draw.polygon(surf, FLAG, [(c[0] + 1, c[1] - 26), (c[0] + 22, c[1] - 20), (c[0] + 1, c[1] - 13)])
        self._text(surf, label, self.font_small, (255, 255, 255), (c[0] + 9, c[1] - 20), anchor='center')
        pygame.draw.circle(surf, (40, 40, 40), c, 3)

    def _rover(self, surf, r: W.Rover, show_sensors: bool, scan: Optional[Sequence[float]],
               arms: bool = False, time_now: float = 0.0):
        if show_sensors:
            cone = pygame.Surface((MAP_PX, MAP_PX), pygame.SRCALPHA)
            pts = [to_px(r.x, r.y)]
            for k in range(13):
                a = r.yaw - W.CAMERA_FOV / 2 + W.CAMERA_FOV * k / 12
                pts.append(to_px(r.x + W.CAMERA_RANGE * math.cos(a), r.y + W.CAMERA_RANGE * math.sin(a)))
            pygame.draw.polygon(cone, (255, 236, 150, 34), pts)
            pygame.draw.lines(cone, (255, 236, 150, 90), True, pts, 1)
            surf.blit(cone, (0, 0))
            if scan:
                ox = r.x + W.LASER_OFFSET * math.cos(r.yaw)
                oy = r.y + W.LASER_OFFSET * math.sin(r.yaw)
                for a, d in zip(W.SCAN_ANGLES, scan):
                    if math.isfinite(d):
                        pygame.draw.circle(surf, (255, 60, 60), to_px(ox + d * math.cos(r.yaw + a),
                                                                      oy + d * math.sin(r.yaw + a)), 2)

        half_l, half_w = W.ROVER_LENGTH / 2, W.ROVER_WIDTH / 2
        for wx in (-0.28, 0.0, 0.28):               # six wheels
            for side in (1, -1):
                pts = [(wx - 0.1, side * (half_w + 0.02)), (wx + 0.1, side * (half_w + 0.02)),
                       (wx + 0.1, side * (half_w - 0.1)), (wx - 0.1, side * (half_w - 0.1))]
                pygame.draw.polygon(surf, WHEEL, self._rotated(pts, r.x, r.y, r.yaw))
        body = [(-half_l, -half_w + 0.06), (half_l, -half_w + 0.06), (half_l, half_w - 0.06), (-half_l, half_w - 0.06)]
        pygame.draw.polygon(surf, ROVER_BODY, self._rotated(body, r.x, r.y, r.yaw))
        deck = [(-half_l + 0.06, -0.17), (0.05, -0.17), (0.05, 0.17), (-half_l + 0.06, 0.17)]
        pygame.draw.polygon(surf, ROVER_DECK, self._rotated(deck, r.x, r.y, r.yaw))
        pygame.draw.polygon(surf, (90, 90, 90), self._rotated(body, r.x, r.y, r.yaw), 1)
        if arms:
            cache = self._rotated([W.CACHE], r.x, r.y, r.yaw)[0]
            tray = pygame.Rect(0, 0, 2 * px(W.CACHE_RADIUS * 0.8), 2 * px(W.CACHE_RADIUS * 0.8))
            tray.center = cache
            pygame.draw.rect(surf, (88, 112, 150), tray, border_radius=max(2, tray.w // 5))
            pygame.draw.rect(surf, (210, 220, 236), tray, 1, border_radius=max(2, tray.w // 5))
            if r.cache:
                self._text(surf, str(len(r.cache)), self.font_small, (255, 255, 255), cache, anchor='center')
        if r.drilling:
            centre = to_px(r.x, r.y)
            for k in range(3):
                a = time_now * 12 + k * 2 * math.pi / 3
                pygame.draw.line(surf, AMBER, centre, (centre[0] + 7 * math.cos(a), centre[1] + 7 * math.sin(a)), 2)
        mast = self._rotated([(0.26, 0.0)], r.x, r.y, r.yaw)[0]
        pygame.draw.circle(surf, (40, 40, 48), mast, 5)
        pygame.draw.circle(surf, AMBER, mast, 2)
        if arms:
            for side in ('left', 'right'):
                pts = self._rotated(W.arm_points(r, side), r.x, r.y, r.yaw)
                width = max(4, px(0.07))
                pygame.draw.lines(surf, (60, 60, 66), False, pts, width + 3)
                pygame.draw.lines(surf, (205, 208, 214), False, pts, width)
                for joint in pts[:2]:
                    pygame.draw.circle(surf, (60, 60, 66), joint, 4)
                    pygame.draw.circle(surf, AMBER, joint, 2)
                # the gripper: two fingers, open or closed
                (ex, ey), (tx, ty) = pts[1], pts[2]
                heading = math.atan2(ty - ey, tx - ex)
                spread = 0.25 if r.holding[side] else 0.7
                for s in (1, -1):
                    a = heading + s * spread
                    finger = max(8, px(0.14))
                    pygame.draw.line(surf, (40, 40, 46), (tx, ty), (tx + finger * math.cos(a), ty + finger * math.sin(a)), 3)
        label_at = to_px(r.x, r.y + 0.75)
        self._text(surf, r.name, self.font_small, (255, 255, 255), label_at, anchor='center', shadow=True)

    def _bubble(self, surf, r: W.Rover, text: str):
        lines = wrap_text(text, self.font_small, 200)[:4]
        w = max(self.font_small.size(line)[0] for line in lines) + 16
        h = 18 * len(lines) + 10
        ax, ay = to_px(r.x, r.y + 0.95)
        rect = pygame.Rect(0, 0, w, h)
        rect.midbottom = (ax, ay - 8)
        rect.clamp_ip(pygame.Rect(2, 2, MAP_PX - 4, MAP_PX - 4))
        pygame.draw.polygon(surf, (255, 255, 255), [(ax - 6, rect.bottom - 1), (ax + 6, rect.bottom - 1), (ax, ay)])
        pygame.draw.rect(surf, (255, 255, 255), rect, border_radius=8)
        pygame.draw.rect(surf, (60, 60, 60), rect, 1, border_radius=8)
        for k, line in enumerate(lines):
            self._text(surf, line, self.font_small, (20, 20, 20), (rect.x + 8, rect.y + 5 + 18 * k))

    # ------------------------------------------------------------------ one frame
    def draw(self, world: W.World, hud: str, goals: List[Tuple[float, float, float]], now: float,
             show_grid: bool = True, show_sensors: bool = True, scans: Optional[Dict[str, List[float]]] = None):
        if self.ground is None or self.ground_version != world.terrain_version:
            self._draw_ground(world, show_grid)
            self.ground_version = world.terrain_version
        surf = self.screen
        surf.blit(self.ground, (0, 0))

        # tyre tracks
        for r in world.rovers.values():
            for x, y, yaw in r.track[::2]:
                for side in (1, -1):
                    tx = x - math.sin(yaw) * side * 0.26
                    ty = y + math.cos(yaw) * side * 0.26
                    pygame.draw.circle(surf, (150, 82, 46), to_px(tx, ty), 2)

        # the lander body sits on the pad
        c = to_px(*W.LANDER)
        for a in (90, 210, 330):
            leg = (c[0] + 28 * math.cos(math.radians(a)), c[1] - 28 * math.sin(math.radians(a)))
            pygame.draw.line(surf, (70, 70, 76), c, leg, 3)
            pygame.draw.circle(surf, (70, 70, 76), leg, 4)
        octagon = [(c[0] + 15 * math.cos(math.radians(22.5 + 45 * k)), c[1] + 15 * math.sin(math.radians(22.5 + 45 * k)))
                   for k in range(8)]
        pygame.draw.polygon(surf, LANDER_BODY, octagon)
        pygame.draw.polygon(surf, (80, 80, 90), octagon, 2)
        self._text(surf, 'LANDER', self.font_small, (255, 255, 255), (c[0], c[1] + px(W.LANDER_RADIUS) + 9),
                   anchor='center', shadow=True)

        for o in world.objects.values():
            if o.kind in W.SOLID:
                self._rock(surf, o)
                if o.kind == 'landmark':
                    self._text(surf, o.id, self.font_small, (255, 255, 255), to_px(o.x, o.y - o.radius - 0.35),
                               anchor='center', shadow=True)
            elif o.kind == 'sample':
                cx, cy = to_px(o.x, o.y)
                s = px(o.radius) + 2
                pygame.draw.polygon(surf, SAMPLE, [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)])
                pygame.draw.polygon(surf, (20, 90, 100), [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)], 1)
                pygame.draw.circle(surf, (230, 255, 255), (cx - 1, cy - 2), 1)
            elif o.kind == 'drill_site':
                cx, cy = to_px(o.x, o.y)
                r_ = px(o.radius)
                depth = world.hole_depth.get(o.id, 0.0)
                if depth > 0:
                    pygame.draw.circle(surf, (110, 58, 30), (cx, cy), max(3, int(r_ * min(1.0, depth / W.CORE_DEPTH))))
                for a in range(0, 360, 30):
                    pygame.draw.arc(surf, (255, 255, 255), (cx - r_, cy - r_, 2 * r_, 2 * r_),
                                    math.radians(a), math.radians(a + 15), 2)
                pygame.draw.line(surf, (255, 255, 255), (cx - 4, cy - 4), (cx + 4, cy + 4), 2)
                pygame.draw.line(surf, (255, 255, 255), (cx - 4, cy + 4), (cx + 4, cy - 4), 2)
            elif o.kind == 'core':
                cx, cy = to_px(o.x, o.y)
                pygame.draw.circle(surf, (236, 228, 214), (cx, cy), px(o.radius) + 1)
                pygame.draw.circle(surf, (150, 96, 60), (cx, cy), px(o.radius) + 1, 2)
                pygame.draw.circle(surf, (190, 120, 80), (cx, cy), 2)
            elif o.kind == 'meteorite':
                cx, cy = to_px(o.x, o.y)
                r_ = px(o.radius)
                pygame.draw.circle(surf, (120, 62, 34), (cx + 3, cy + 3), r_)
                pygame.draw.circle(surf, (58, 58, 68), (cx, cy), r_)
                pygame.draw.circle(surf, (96, 96, 110), (cx - r_ // 3, cy - r_ // 3), r_ // 3)
                for dx, dy in ((r_ // 3, r_ // 4), (-r_ // 5, r_ // 2), (r_ // 2, -r_ // 3)):
                    pygame.draw.circle(surf, (40, 40, 48), (cx + dx, cy + dy), max(2, r_ // 6))
                pygame.draw.circle(surf, (30, 30, 36), (cx, cy), r_, 1)

        for k, (x, y, radius) in enumerate(goals):
            self._flag(surf, x, y, radius, str(k + 1) if len(goals) > 1 or k == 0 else '')

        for r in world.rovers.values():
            self._rover(surf, r, show_sensors, (scans or {}).get(r.name), world.arms, now)
        for r in world.rovers.values():
            for side in ('left', 'right'):
                held = world.objects.get(r.holding[side])
                if held is not None and held.kind != 'meteorite':
                    cx, cy = to_px(held.x, held.y)
                    colour = SAMPLE if held.kind == 'sample' else (236, 228, 214)
                    pygame.draw.circle(surf, colour, (cx, cy), px(held.radius) + 1)
                    pygame.draw.circle(surf, (40, 40, 46), (cx, cy), px(held.radius) + 1, 1)
        for r in world.rovers.values():
            if r.radio and now - r.radio_time < 5.0:
                self._bubble(surf, r, r.radio)

        self._panel(world, hud)
        pygame.display.flip()

    # ------------------------------------------------------------------ the panel on the right
    def _panel(self, world: W.World, hud: str):
        x0 = MAP_PX
        surf = self.screen
        pygame.draw.rect(surf, PANEL, (x0, 0, PANEL_PX, MAP_PX))
        pygame.draw.line(surf, (12, 26, 40), (x0, 0), (x0, MAP_PX), 3)
        y = 14
        self._text(surf, 'MARS ROVER ACADEMY', self.font_title, AMBER, (x0 + 16, y))
        y += 34
        width = PANEL_PX - 32

        for raw in (hud or 'Waiting for mission control...').splitlines():
            if raw.startswith('# '):
                for line in wrap_text(raw[2:], self.font_bold, width):
                    self._text(surf, line, self.font_bold, (255, 255, 255), (x0 + 16, y))
                    y += 22
            elif raw.startswith('[x] ') or raw.startswith('[ ] '):
                done = raw.startswith('[x]')
                box = pygame.Rect(x0 + 16, y + 3, 12, 12)
                pygame.draw.rect(surf, GREEN if done else PANEL_DIM, box, 0 if done else 1, border_radius=2)
                if done:
                    pygame.draw.lines(surf, PANEL, False, [(box.x + 2, box.y + 6), (box.x + 5, box.y + 9), (box.x + 10, box.y + 2)], 2)
                for k, line in enumerate(wrap_text(raw[4:], self.font, width - 20)):
                    self._text(surf, line, self.font, GREEN if done else PANEL_TEXT, (x0 + 36, y))
                    y += 19
            elif raw.startswith('* '):
                for line in wrap_text(raw[2:], self.font_mono, width):
                    self._text(surf, line, self.font_mono, CYAN, (x0 + 16, y))
                    y += 17
            elif raw.startswith('! '):
                for line in wrap_text(raw[2:], self.font, width):
                    self._text(surf, line, self.font, RED, (x0 + 16, y))
                    y += 19
            elif raw.startswith('$ '):
                stars = int(raw[2:] or 0)
                for k in range(3):
                    self._star(surf, (x0 + 30 + 34 * k, y + 14), 13, AMBER if k < stars else (70, 90, 110))
                y += 34
            elif raw == '':
                y += 8
            else:
                for line in wrap_text(raw, self.font, width):
                    self._text(surf, line, self.font, PANEL_DIM, (x0 + 16, y))
                    y += 19

        # rover status at the bottom
        rovers = list(world.rovers.values())[:2]
        block = 78 if world.arms else 62
        y = MAP_PX - 16 - block * len(rovers)
        for r in rovers:
            pygame.draw.line(surf, (40, 66, 90), (x0 + 16, y - 8), (x0 + PANEL_PX - 16, y - 8))
            self._text(surf, r.name, self.font_bold, (255, 255, 255), (x0 + 16, y))
            self._text(surf, f'x {r.x:5.2f}  y {r.y:5.2f}  yaw {math.degrees(r.yaw):4.0f}°',
                       self.font_mono, PANEL_DIM, (x0 + 16, y + 22))
            self._text(surf, f'v {r.v:4.2f} m/s  w {r.w:5.2f} rad/s', self.font_mono, PANEL_DIM, (x0 + 16, y + 38))
            bar = pygame.Rect(x0 + PANEL_PX - 116, y + 3, 80, 14)
            level = GREEN if r.battery > 0.3 else AMBER if r.battery > 0.1 else RED
            pygame.draw.rect(surf, (40, 60, 80), bar, border_radius=3)
            pygame.draw.rect(surf, level, (bar.x, bar.y, int(bar.w * r.battery), bar.h), border_radius=3)
            pygame.draw.rect(surf, PANEL_DIM, bar, 1, border_radius=3)
            pygame.draw.rect(surf, PANEL_DIM, (bar.right, bar.y + 4, 3, 6))
            charge = '+' if world.charging(r) else ''
            self._text(surf, f'{r.battery * 100:3.0f}%{charge}', self.font_small, PANEL_TEXT, (bar.right + 6, y + 3))
            if world.arms:
                hot = r.drill_temp > 60
                drill = 'broken' if r.drill_broken else f'{r.drill_temp:3.0f} C'
                self._text(surf, f'cache {len(r.cache)}/{W.CACHE_CAPACITY}  drill {drill}', self.font_mono,
                           RED if (hot or r.drill_broken) else PANEL_DIM, (x0 + 16, y + 54))
            y += block

    def _star(self, surf, centre, radius, colour):
        pts = []
        for k in range(10):
            rr = radius if k % 2 == 0 else radius * 0.45
            a = -math.pi / 2 + k * math.pi / 5
            pts.append((centre[0] + rr * math.cos(a), centre[1] + rr * math.sin(a)))
        pygame.draw.polygon(surf, colour, pts)

    def save(self, path: str):
        pygame.image.save(self.screen, path)

    def closed(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
        return False


def wrap_text(text: str, font: pygame.font.Font, width: int) -> List[str]:
    lines, line = [], ''
    for word in text.split(' '):
        trial = f'{line} {word}' if line else word
        if font.size(trial)[0] <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines
