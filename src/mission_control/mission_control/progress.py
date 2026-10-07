"""Star board: best result per mission, saved in ~/.mars_rover_academy/progress.json.

    ros2 run mission_control progress          # show the board
    ros2 run mission_control progress --reset  # start over
"""

import json
import sys
from pathlib import Path

from mission_control.missions import MISSIONS

PROGRESS_FILE = Path.home() / '.mars_rover_academy' / 'progress.json'


def load() -> dict:
    try:
        return json.loads(PROGRESS_FILE.read_text())
    except (OSError, ValueError):
        return {}


def record(mission: int, stars: int, seconds: float) -> dict:
    """Keep the best result (more stars, then faster) and return it."""
    data = load()
    key = str(mission)
    best = data.get(key)
    if best is None or (stars, -seconds) > (best['stars'], -best['time']):
        best = {'stars': stars, 'time': round(seconds, 1)}
        data[key] = best
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PROGRESS_FILE.write_text(json.dumps(data, indent=2))
    return best


def main():
    if '--reset' in sys.argv:
        PROGRESS_FILE.unlink(missing_ok=True)
        print('Progress reset.')
        return
    data = load()
    total = 0
    print('\n  MARS ROVER ACADEMY -- star board\n')
    for number, mission in sorted(MISSIONS.items()):
        best = data.get(str(number))
        if best:
            total += best['stars']
            stars = '⭐' * best['stars'] + '☆' * (3 - best['stars'])
            print(f'  {number:2d}  {stars}  {best["time"]:7.1f} s   {mission.title}')
        else:
            print(f'  {number:2d}  ☆☆☆        --     {mission.title}')
    print(f'\n  total: {total} / {3 * len(MISSIONS)} ⭐\n')
    todo = [n for n in sorted(MISSIONS) if str(n) not in data]
    if todo:
        print(f'  next: ros2 launch mission_control mission.launch.py mission:={todo[0]}\n')


if __name__ == '__main__':
    main()
