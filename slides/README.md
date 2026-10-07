# Slides

All decks are [Marp](https://marp.app/) Markdown. Every slide has speaker notes (the HTML comments) with timing, what to say,
what learners should see and the usual mistakes.

| Deck | For |
|---|---|
| `mars-rover-course.md` | **the whole course in one deck**: for every mission an overview, a picture of the system you build (its system map), how to run it, the key code and a checklist |
| `ros2-in-one-hour.md` | a one-hour introduction for the first session: 27 slides, seven live demos |
| `missions/00-landing.md` … `missions/08-boss-power-crisis.md` | the long version of Part 1: every step of every guide, one deck per mission |

Each deck in `missions/` follows the same order:

1. title and a roadmap of Part 1, with finished missions ticked (✓) and today's mission marked (▶)
2. today's goal: objectives, stars and a screenshot
3. the concepts, then the guide's steps in order (the header shows "Step k of n")
4. hints and solutions on separate slides, so you can skip them until people have tried
5. the system map, "Check yourself" questions (answers in the notes) and a checklist slide
6. the roadmap again, pointing to the next mission

The checklist slides match [CHECKLIST.md](../CHECKLIST.md), which learners can copy and tick off as they go.
Every command and line of code on the slides is copied from the mission guides, so slides and guides never disagree.
Decks for Part 2 (missions 9 to 12) don't exist yet; `mars-rover-course.md` covers them.

## Presenting

The easiest way is VS Code with the **Marp for VS Code** extension: open the file and use the preview, or export from the
command palette (*Marp: Export slide deck*).

From the terminal, with Node.js installed:

```bash
cd slides
npx @marp-team/marp-cli ros2-in-one-hour.md --allow-local-files --pdf       # PDF
npx @marp-team/marp-cli ros2-in-one-hour.md --allow-local-files --pptx      # PowerPoint
npx @marp-team/marp-cli ros2-in-one-hour.md --allow-local-files -o deck.html # HTML, press P for presenter view
```

`--allow-local-files` is needed because the slides use the mission screenshots from `../docs/images/mars/`.

## Before the session

- Build the workspace, and the instructor-only `rover_solutions` package (demos 5 to 7 use it; see [TEACHER.md](../TEACHER.md#solutions)).
- `sudo apt install ros-$ROS_DISTRO-teleop-twist-keyboard` for demo 1.
- Set your own `ROS_DOMAIN_ID`, so nobody else in the room can drive your rover.
- `rqt_graph` (demo 2) is optional: `sudo apt install ros-$ROS_DISTRO-rqt-graph`.

If time runs short, skip from *Topic or service?* (slide 12) to *Which one do I need?* (slide 23).

## Diagrams

The diagrams in `images/` are rendered from the Mermaid sources in `diagrams/`, in the same colours as the system maps in the
mission guides. `images/missions/` holds the system maps of the mission guides, rendered from the Mermaid blocks in `missions/*.md`.
After editing a source, render it again with [mermaid-cli](https://github.com/mermaid-js/mermaid-cli):

```bash
npx @mermaid-js/mermaid-cli -i diagrams/topics.mmd -o images/topics.png -b transparent -s 2
```

## Theme

`mars-rover-course.md` uses Marp's built-in `gaia` theme with the rules of
[marp-theme-academic](https://github.com/kaisugi/marp-theme-academic) by Kaito Sugimoto, copied into the deck's `style:` with
the colours changed. No extra setup is needed in VS Code or marp-cli. Its licence:

```text
MIT License

Copyright (c) 2022 Kaito Sugimoto

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
