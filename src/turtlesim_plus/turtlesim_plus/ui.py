#!/usr/bin/python3

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Drawing helpers for the teaching overlays: coordinate grid, speech bubbles,
goal flags and the info panel. Kept separate from entity.py so the simulation
model stays free of presentation details."""

import functools
import math
import unicodedata
from typing import Dict, List, Tuple

import pygame

from turtlesim_plus.world import (
    WORLD_SIZE, SCREEN_SIZE, PANEL_WIDTH, world_to_screen, world_length_to_screen
)

# Fonts that cover both Thai and Latin come first (Noto Sans Thai is deliberately
# absent: it has no Latin glyphs). pygame's bundled default font has no Thai, so
# Thai text renders as boxes without one of these (apt: fonts-tlwg-loma etc.).
_FONT_CANDIDATES = ['waree', 'loma', 'garuda', 'umpush', 'kinnari', 'freesans', 'dejavusans']
_font_cache: Dict[Tuple[int, bool], pygame.font.Font] = {}
_text_cache: Dict[tuple, pygame.Surface] = {}
_grid_surface = None

WHITE = (240, 240, 240)
GREY = (150, 150, 160)
DIM = (70, 70, 80)
YELLOW = (255, 210, 60)
GREEN = (90, 220, 120)
ORANGE = (255, 150, 60)
CYAN = (90, 200, 255)
PANEL_BG = (24, 26, 36)


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _font_cache:
        font = None
        for name in _FONT_CANDIDATES:
            path = pygame.font.match_font(name, bold=bold)
            if path:
                font = pygame.font.Font(path, size)
                break
        if font is None:
            font = pygame.font.Font(None, size + 4)
        try:
            font.set_script('Thai')  # needs SDL_ttf built with HarfBuzz; harmless otherwise
        except (AttributeError, pygame.error):
            pass
        _font_cache[key] = font
    return _font_cache[key]


def render_text(text: str, size: int, color, bold: bool = False) -> pygame.Surface:
    """font.render with a cache -- most panel/label text is identical frame to frame."""
    key = (text, size, color, bold)
    surf = _text_cache.get(key)
    if surf is None:
        if len(_text_cache) > 1000:
            _text_cache.clear()
        surf = _text_cache[key] = get_font(size, bold).render(text, True, color)
    return surf


def wrap_text(text: str, font: pygame.font.Font, width: int) -> List[str]:
    """Greedy wrap that also works for Thai (no spaces between words): falls back
    to breaking between characters, but never in front of a combining mark."""
    lines = []
    current = ''
    for ch in text:
        candidate = current + ch
        if font.size(candidate)[0] <= width or not current or unicodedata.combining(ch):
            current = candidate
            continue
        cut = current.rfind(' ')
        if cut > 0:
            lines.append(current[:cut])
            current = current[cut + 1:] + ch
        else:
            # step back over trailing combining marks so they stay with their base
            i = len(current)
            while i > 1 and unicodedata.combining(current[i - 1]):
                i -= 1
            lines.append(current[:i])
            current = current[i:] + ch
    lines.append(current)
    return lines


@functools.lru_cache(maxsize=512)
def wrap_cached(text: str, size: int, bold: bool, width: int) -> Tuple[str, ...]:
    return tuple(wrap_text(text, get_font(size, bold), width))


def draw_grid(screen):
    global _grid_surface
    if _grid_surface is None:  # static, so draw it once and reuse
        _grid_surface = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE))
        font = get_font(11)
        for i in range(1, int(WORLD_SIZE) + 1):
            x, _ = world_to_screen(i, 0)
            _, y = world_to_screen(0, i)
            color = (48, 48, 58) if i % 5 else (75, 75, 90)
            pygame.draw.line(_grid_surface, color, (x, 0), (x, SCREEN_SIZE))
            pygame.draw.line(_grid_surface, color, (0, y), (SCREEN_SIZE, y))
            _grid_surface.blit(font.render(str(i), True, DIM), (x + 2, SCREEN_SIZE - 14))
            _grid_surface.blit(font.render(str(i), True, DIM), (2, y - 13))
        _grid_surface.blit(font.render('0', True, DIM), (2, SCREEN_SIZE - 14))
    screen.blit(_grid_surface, (0, 0))


def draw_label(screen, text: str, center: Tuple[float, float], color=GREY, size: int = 12):
    surf = render_text(text, size, color)
    screen.blit(surf, (center[0] - surf.get_width() / 2, center[1] - surf.get_height() / 2))


def draw_speech_bubble(screen, text: str, anchor: Tuple[float, float]):
    lines = []
    for paragraph in text.split('\n'):
        lines.extend(wrap_cached(paragraph, 15, False, 200))
    surfs = [render_text(line, 15, (20, 20, 20)) for line in lines]
    pad = 7
    w = max(s.get_width() for s in surfs) + 2 * pad
    h = sum(s.get_height() for s in surfs) + 2 * pad
    ax, ay = anchor
    x = min(max(ax - w / 2, 2), SCREEN_SIZE - w - 2)
    y = ay - 34 - h
    if y < 2:  # no room above the turtle -> show it below
        y = ay + 34
    rect = pygame.Rect(int(x), int(y), int(w), int(h))
    tail_y = rect.bottom if y < ay else rect.top
    tail_tip = (ax, ay - 22) if y < ay else (ax, ay + 22)
    pygame.draw.polygon(screen, WHITE, [(ax - 7, tail_y), (ax + 7, tail_y), tail_tip])
    pygame.draw.rect(screen, WHITE, rect, border_radius=9)
    cy = rect.top + pad
    for s in surfs:
        screen.blit(s, (rect.left + pad, cy))
        cy += s.get_height()


def draw_goal(screen, index: int, x: float, y: float, radius: float, is_next: bool):
    cx, cy = world_to_screen(x, y)
    r = max(6, int(world_length_to_screen(radius)))
    color = YELLOW if is_next else GREY
    ring = pygame.Surface((2 * r + 2, 2 * r + 2), pygame.SRCALPHA)
    pygame.draw.circle(ring, (*color, 45), (r + 1, r + 1), r)
    pygame.draw.circle(ring, (*color, 200), (r + 1, r + 1), r, 2)
    screen.blit(ring, (cx - r - 1, cy - r - 1))
    # little flag: pole + pennant
    pygame.draw.line(screen, color, (cx, cy), (cx, cy - 22), 2)
    pygame.draw.polygon(screen, color, [(cx, cy - 22), (cx + 14, cy - 17), (cx, cy - 12)])
    draw_label(screen, str(index), (cx - 9, cy - 17), color=color, size=13)


def draw_star(screen, center: Tuple[float, float], radius: float, color, filled: bool = True):
    points = []
    for i in range(10):
        r = radius if i % 2 == 0 else radius * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        points.append((center[0] + r * math.cos(a), center[1] + r * math.sin(a)))
    pygame.draw.polygon(screen, color if filled else DIM, points, 0 if filled else 2)


def draw_panel(screen, hud_text: str, turtles: List[dict]):
    """Right-hand info panel: mission HUD (if a mission is running) + live turtle status.

    hud_text uses a tiny line-prefix markup so a mission node can style it with a
    plain std_msgs/String: '# ' title, '[x] ' done, '[ ] ' todo, '! ' warning,
    '* ' highlight, '$ N' an N-of-3 star rating, anything else is body text.
    """
    left = SCREEN_SIZE
    pygame.draw.rect(screen, PANEL_BG, pygame.Rect(left, 0, PANEL_WIDTH, SCREEN_SIZE))
    pygame.draw.line(screen, (60, 60, 80), (left, 0), (left, SCREEN_SIZE), 2)
    x0 = left + 12
    width = PANEL_WIDTH - 24
    y = 10
    screen.blit(render_text('TURTLESIM+', 20, CYAN, bold=True), (x0, y))
    y += 32

    if not hud_text:
        hud_text = ('No mission running.\n'
                    '* ros2 launch turtle_quest mission.launch.py mission:=0')
    for raw in hud_text.split('\n'):
        color, indent, box = WHITE, 0, None
        size, bold = 14, False
        text = raw
        if raw.startswith('# '):
            color, text, size, bold = YELLOW, raw[2:], 16, True
        elif raw.startswith('[x] '):
            color, indent, box, text = GREEN, 20, True, raw[4:]
        elif raw.startswith('[ ] '):
            indent, box, text = 20, False, raw[4:]
        elif raw.startswith('! '):
            color, text = ORANGE, raw[2:]
        elif raw.startswith('* '):
            color, text = CYAN, raw[2:]
        if raw.startswith('$ '):  # star rating, e.g. '$ 2' -> two filled stars out of three
            filled = int(raw[2:].strip() or 0)
            for i in range(3):
                draw_star(screen, (x0 + 16 + i * 36, y + 16), 14, YELLOW, filled=i < filled)
            y += 36
            continue
        if not text.strip():
            y += 6
            continue
        for i, line in enumerate(wrap_cached(text, size, bold, width - indent)):
            if y > SCREEN_SIZE - 20:
                break
            if box is not None and i == 0:
                rect = pygame.Rect(x0, y + 4, 12, 12)
                pygame.draw.rect(screen, color, rect, 0 if box else 1, border_radius=2)
                if box:
                    pygame.draw.lines(screen, PANEL_BG, False,
                                      [(rect.left + 2, rect.centery), (rect.left + 5, rect.bottom - 3),
                                       (rect.right - 2, rect.top + 3)], 2)
            surf = render_text(line, size, color, bold)
            screen.blit(surf, (x0 + indent, y))
            y += surf.get_height() + 1

    # live status block, pinned to the bottom of the panel
    small = get_font(13)
    lines_per_turtle = 3 if any(t.get('arms') for t in turtles) else 2
    row_h = small.get_linesize() * lines_per_turtle + 4
    y = max(y + 12, SCREEN_SIZE - 26 - row_h * len(turtles))
    if y > SCREEN_SIZE - 30:
        return
    pygame.draw.line(screen, (60, 60, 80), (x0, y), (left + PANEL_WIDTH - 12, y))
    y += 6
    for t in turtles:
        if y > SCREEN_SIZE - row_h:
            break
        head = f"{t['name']}  x={t['x']:.2f}  y={t['y']:.2f}  th={math.degrees(t['theta']):.0f}°"
        screen.blit(render_text(head, 13, WHITE), (x0, y))
        y += small.get_linesize()
        info = f"   pizza={t['pizza']}  parcel={t['parcel']}" + ('  [carrying]' if t['carrying'] else '')
        screen.blit(render_text(info, 13, GREY), (x0, y))
        if t.get('arms'):
            y += small.get_linesize()
            screen.blit(render_text(t['arms'], 13, GREY), (x0, y))
        y += small.get_linesize() + 4
