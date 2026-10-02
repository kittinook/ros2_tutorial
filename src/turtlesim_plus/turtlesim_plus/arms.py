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

"""Dual-arm turtles: two planar 2-link arms with grippers, plus the Crate object.

Arm geometry, in the turtle's own frame (x forward, y left, angles in radians):

    shoulder base  = (0, +BASE_OFFSET) for the left arm, (0, -BASE_OFFSET) for the right
    elbow          = base  + L1 * (cos(q1),      sin(q1))
    tip (gripper)  = elbow + L2 * (cos(q1 + q2), sin(q1 + q2))

q1 = shoulder angle measured from the turtle's heading, q2 = elbow angle relative
to the upper arm. Joints are position-controlled: a command sets a target and the
joint moves towards it at a limited speed.
"""

import math
from typing import Dict, List, Optional, Tuple

import pygame

from turtlesim_plus.entity import Entity, GraphicsEntity, Pizza, Parcel
from turtlesim_plus.world import world_to_screen, world_length_to_screen

BASE_OFFSET = 0.3   # sideways distance from the turtle's centre to each shoulder
L1 = 0.8            # upper arm length
L2 = 0.7            # forearm length
SHOULDER_LIMIT = math.pi
ELBOW_LIMIT = 2.7
GRASP_RADIUS = 0.4  # how close the tip must be to a pizza/parcel to grab it
CRATE_SIZE = 0.8    # crate side length
CRATE_GRASP = CRATE_SIZE / 2 + 0.25   # tip-to-crate-centre distance that still counts as touching it
CRATE_MAX_SPAN = 1.5                  # grippers further apart than this and the crate slips
JOINT_NAMES = ['left_shoulder', 'left_elbow', 'right_shoulder', 'right_elbow']
# tucked-in starting posture (q1, q2): tips end up just in front of the shoulders
HOME = {'left': (1.2, -2.4), 'right': (-1.2, 2.4)}
ARM_COLORS = {'left': (255, 170, 60), 'right': (90, 200, 255)}


def to_world(pose: List[float], local: Tuple[float, float]) -> Tuple[float, float]:
    """Turtle-frame point -> world point."""
    c, s = math.cos(pose[2]), math.sin(pose[2])
    return pose[0] + c * local[0] - s * local[1], pose[1] + s * local[0] + c * local[1]


class Crate(GraphicsEntity):
    """A heavy box: it only moves while BOTH grippers of the same turtle hold it."""

    def __init__(self, name: str, pose: List[float]):
        super().__init__(name)
        self.pose = pose
        self.holders: List[str] = []  # e.g. ['turtle1/left', 'turtle1/right']

    def render(self, screen):
        cx, cy = world_to_screen(self.pose[0], self.pose[1])
        half = world_length_to_screen(CRATE_SIZE) / 2
        rect = pygame.Rect(int(cx - half), int(cy - half), int(2 * half), int(2 * half))
        lifted = len(self.holders) == 2
        pygame.draw.rect(screen, (190, 135, 70) if lifted else (160, 110, 55), rect, border_radius=3)
        pygame.draw.rect(screen, (95, 60, 25), rect, 3, border_radius=3)
        pygame.draw.line(screen, (95, 60, 25), rect.topleft, rect.bottomright, 2)
        pygame.draw.line(screen, (95, 60, 25), rect.topright, rect.bottomleft, 2)


class Arm:
    """One 2-link arm + gripper. Pure kinematics/state; no ROS in here."""

    def __init__(self, side: str):
        self.side = side
        self.sign = 1.0 if side == 'left' else -1.0
        self.q = list(HOME[side])          # current joint angles [shoulder, elbow]
        self.target = list(HOME[side])     # commanded joint angles
        self.velocity = [0.0, 0.0]
        self.held: Optional[Entity] = None
        self.closed = False

    @staticmethod
    def clamp_target(index: int, value: float) -> float:
        limit = SHOULDER_LIMIT if index == 0 else ELBOW_LIMIT
        return min(max(value, -limit), limit)

    def step(self, dt: float, max_speed: float):
        for i in range(2):
            error = self.target[i] - self.q[i]
            move = max(-max_speed * dt, min(max_speed * dt, error))
            self.q[i] += move
            self.velocity[i] = move / dt if dt > 0 else 0.0

    def points_local(self) -> List[Tuple[float, float]]:
        """base, elbow, tip in the turtle frame."""
        q1, q2 = self.q
        base = (0.0, self.sign * BASE_OFFSET)
        elbow = (base[0] + L1 * math.cos(q1), base[1] + L1 * math.sin(q1))
        tip = (elbow[0] + L2 * math.cos(q1 + q2), elbow[1] + L2 * math.sin(q1 + q2))
        return [base, elbow, tip]

    def tip_world(self, pose: List[float]) -> Tuple[float, float]:
        return to_world(pose, self.points_local()[2])

    def render(self, screen, pose: List[float]):
        pts = [world_to_screen(*to_world(pose, p)) for p in self.points_local()]
        color = ARM_COLORS[self.side]
        dark = tuple(c // 2 for c in color)
        pygame.draw.line(screen, color, pts[0], pts[1], 7)
        pygame.draw.line(screen, color, pts[1], pts[2], 5)
        for p in pts[:2]:
            pygame.draw.circle(screen, dark, p, 5)
        # gripper: two fingers around the tip, wide open or pinched shut
        heading = pose[2] + self.q[0] + self.q[1]
        spread = 0.25 if self.closed else 0.7
        for k in (-1, 1):
            a = heading + k * spread
            # screen y is flipped, hence the minus on sin
            end = (pts[2][0] + 11 * math.cos(a), pts[2][1] - 11 * math.sin(a))
            pygame.draw.line(screen, dark, pts[2], end, 3)
        pygame.draw.circle(screen, dark, pts[2], 4)


class DualArms:
    """Both arms of one turtle, the grasping rules, and how held objects follow the grippers."""

    def __init__(self, owner: str):
        self.owner = owner
        self.arms: Dict[str, Arm] = {'left': Arm('left'), 'right': Arm('right')}

    def set_targets(self, names: List[str], positions: List[float]) -> List[str]:
        """Apply a joint command; returns the names that were not recognised."""
        unknown = []
        for name, value in zip(names, positions):
            side, _, joint = name.partition('_')
            if side in self.arms and joint in ('shoulder', 'elbow'):
                index = 0 if joint == 'shoulder' else 1
                self.arms[side].target[index] = Arm.clamp_target(index, value)
            else:
                unknown.append(name)
        return unknown

    def joint_positions(self) -> List[float]:
        return [*self.arms['left'].q, *self.arms['right'].q]

    def joint_velocities(self) -> List[float]:
        return [*self.arms['left'].velocity, *self.arms['right'].velocity]

    def grasp(self, side: str, pose: List[float], entity_list: Dict[str, Entity]) -> Tuple[bool, str]:
        arm = self.arms[side]
        arm.closed = True
        if arm.held is not None:
            return True, f'already holding {arm.held.name}'
        tip = arm.tip_world(pose)
        holder = f'{self.owner}/{side}'
        best, best_d = None, float('inf')
        for e in entity_list.values():
            if isinstance(e, Crate):
                reach = CRATE_GRASP
                free = all(h.startswith(self.owner + '/') for h in e.holders)  # nobody else's hands on it
            elif isinstance(e, (Pizza, Parcel)):
                reach = GRASP_RADIUS
                free = not getattr(e, 'held_by', '')
            else:
                continue
            d = math.hypot(e.pose[0] - tip[0], e.pose[1] - tip[1])
            if free and d <= reach and d < best_d:
                best, best_d = e, d
        if best is None:
            return False, 'nothing within reach of the gripper'
        arm.held = best
        if isinstance(best, Crate):
            best.holders.append(holder)
            if len(best.holders) < 2:
                return True, f'gripping {best.name} -- it is too heavy for one arm, grab it with the other arm too'
        else:
            best.held_by = holder
        return True, f'grabbed {best.name}'

    def release(self, side: str) -> Tuple[bool, str]:
        arm = self.arms[side]
        arm.closed = False
        if arm.held is None:
            return True, 'gripper opened (it was empty)'
        name = arm.held.name
        self._drop(side)
        return True, f'released {name}'

    def _drop(self, side: str):
        arm = self.arms[side]
        e = arm.held
        arm.held = None
        if isinstance(e, Crate):
            holder = f'{self.owner}/{side}'
            if holder in e.holders:
                e.holders.remove(holder)
        elif e is not None:
            e.held_by = ''

    def release_all(self):
        for side in self.arms:
            self._drop(side)

    def holding(self, side: str) -> str:
        held = self.arms[side].held
        return type(held).__name__ if held is not None else ''

    def update(self, dt: float, max_speed: float, pose: List[float], entity_list: Dict[str, Entity], log=None):
        for side, arm in self.arms.items():
            arm.step(dt, max_speed)
            # the object may have been eaten / picked up / cleared meanwhile
            if arm.held is not None and entity_list.get(arm.held.name) is not arm.held:
                arm.held = None
        tips = {side: arm.tip_world(pose) for side, arm in self.arms.items()}
        left, right = self.arms['left'].held, self.arms['right'].held
        for side, arm in self.arms.items():
            if arm.held is not None and not isinstance(arm.held, Crate):
                arm.held.pose = [tips[side][0], tips[side][1], 0.0]
        if isinstance(left, Crate) and left is right:
            span = math.hypot(tips['left'][0] - tips['right'][0], tips['left'][1] - tips['right'][1])
            if span > CRATE_MAX_SPAN:
                if log:
                    log(f'{self.owner}: {left.name} slipped -- the grippers moved too far apart')
                self.release_all()
                for arm in self.arms.values():
                    arm.closed = False
            else:
                left.pose = [(tips['left'][0] + tips['right'][0]) / 2, (tips['left'][1] + tips['right'][1]) / 2, 0.0]

    def render(self, screen, pose: List[float]):
        for arm in self.arms.values():
            arm.render(screen, pose)


def panel_text(arms: DualArms) -> str:
    def show(side):
        return arms.holding(side) or '-'
    return f"   L: {show('left')}   R: {show('right')}"
