# Mars Rover: ร่างสเปก (design draft)

> สถานะ: **เสร็จครบ 4 เฟส** ภารกิจ 0–12 มีเฉลยและทดสอบผ่านบน Humble และ Jazzy, เอกสารและ slides อัปเดตเป็น Mars Rover แล้ว
>
> ตัดสินใจแล้ว: rover มี **2 แขน + สว่าน**, ใช้ชื่อตามหัวข้อ 2
>
> แก้ไฟล์นี้หรือคอมเมนต์ได้เลย พอตกลงกันแล้วจะใช้เป็นแบบในการเขียน simulator, mission_control และเนื้อหา 13 ภารกิจ

## 1. ภาพรวม

**คงเดิม:** วิธีสอนทั้งหมด
- ภารกิจ 13 บท แบ่ง 2 part
- simulator 2D มุมบนด้วย pygame รันบนโน้ตบุ๊กธรรมดาได้
- node ผู้คุมภารกิจที่ตรวจงานผ่าน ROS interface ล้วน ๆ ให้ดาว 1–3 ดวง และจับ teleop หรือ `ros2 topic pub` ในภารกิจเขียนโค้ด
- รูปแบบเอกสาร: overview → the picture → run it → checklist, system map สีเดิม, CONCEPTS, CHECKLIST และ slides

**ใหม่:** simulator เขียนเองทั้งหมด และใช้ ROS interface แบบเดียวกับหุ่นจริง

| | Mars Rover |
|---|---|
| ตำแหน่ง | `nav_msgs/Odometry` (quaternion, velocity) |
| เซนเซอร์ | `sensor_msgs/LaserScan` ของจริง + กล้องตรวจจับวัตถุ |
| พลังงาน | `sensor_msgs/BatteryState` หมดได้จริง ต้องกลับไปชาร์จ |
| การเคลื่อนที่ | มีความเร่งจำกัด ลื่นบนทราย ชนหินแล้วหยุด |
| เฟรมพิกัด | **tf2** จริง เปิดดูใน RViz ได้ |
| action | **action client ในโค้ด** (เจาะหิน: feedback และ cancel) |
| แขน | 2 แขนหน้ารถ + สว่านใต้ท้อง + ถาดเก็บตัวอย่าง, ตำแหน่งปลายแขนอ่านจาก tf2 |
| teleop | `teleop_twist_keyboard` (เครื่องมือที่ใช้กับหุ่นจริง) + remap |

## 2. ชื่อ (เสนอ)

| สิ่ง | ชื่อ |
|---|---|
| คอร์ส | **Mars Rover Academy** |
| simulator | package `mars_sim`, node `mars_sim` |
| interfaces | package `mars_interfaces` |
| ผู้คุมภารกิจ (แทน quest_master) | package และ node `mission_control` |
| package ของผู้เรียน | `my_rover` |

```bash
ros2 launch mission_control mission.launch.py mission:=0
```

## 3. โลก

- ขนาด **20 × 20 m** จุด (0, 0) อยู่มุมล่างซ้าย, +x ไปทางขวา, +y ขึ้น frame ชื่อ `map`
- **Lander (ฐาน):** วงกลมรัศมี 1.5 m ที่ (3, 3) เป็นจุดชาร์จแบตและส่งตัวอย่าง
- **หิน (rock):** วงกลมทึบ รถชนแล้วหยุด (นับเป็น bump) และ LaserScan มองเห็น
- **ทราย (sand):** พื้นทรายสีอ่อนมีลายคลื่น รถลื่น ได้ความเร็วจริงแค่ ~60% ของที่สั่ง ทำให้ open loop พลาด
- **Crater:** พื้นต่ำ ขับผ่านได้แต่ช้า
- **วัตถุในภารกิจ:** beacon (ธง), landmark (จุดถ่ายรูป), sample (หินตัวอย่างเล็ก), drill site (จุดเจาะ), core (แท่งตัวอย่างหลังเจาะ)
- หน้าจอ: แผนที่สีสนิมดาวอังคาร + แผงขวาแสดงภารกิจ เวลา ตำแหน่ง และแถบแบตเตอรี่ มี grid เป็นเมตรเหมือนเดิม

## 4. Rover

| | ค่า |
|---|---|
| รูปทรง | differential drive, 0.8 × 0.6 m |
| ความเร็วสูงสุด | 1.0 m/s, 2.0 rad/s |
| ความเร่ง | จำกัดที่ 1.0 m/s², 3.0 rad/s² |
| cmd_vel timeout | 1.0 s (คง "1-second rule" ไว้สอนในภารกิจ 2 และเล่าว่าหุ่นจริงก็มี watchdog แบบนี้) ความเร่งขึ้นและลงเท่ากัน ระยะทางจึงยังเท่ากับ ความเร็ว × จำนวนวินาทีที่สั่ง พอดี เช่น `--rate 1 --times 5` ที่ 1.0 m/s = 5 m |
| กล้อง | มุม 60°, ระยะ 6 m, บอกชนิด, ระยะ และมุมของวัตถุ |
| LaserScan | ด้านหน้า 180°, 181 ลำแสง, 0.15–8 m, 10 Hz เห็นหินและขอบโลก |
| แบตเตอรี่ | หมดตามระยะขับ (0.2%/m) เวลา idle (0.02%/s) และการเจาะ ชาร์จ 3%/s เมื่อจอดนิ่งบน lander ถ้าหมด รถหยุดและภารกิจล้มเหลว ภารกิจทั่วไปแทบไม่กินแบต boss ภารกิจ 8 ตั้ง `battery_drain` ให้สูงขึ้น |
| แขน (Part 2) | 2 แขน ซ้ายและขวา แต่ละแขนมี 2 ข้อต่อบนระนาบ ฐานแขนอยู่ที่ (0.4, ±0.25) ใน `base_link`, L1 = 0.6 m, L2 = 0.5 m ข้อต่อ `left_shoulder`, `left_elbow`, `right_shoulder`, `right_elbow` แต่ละแขนมี gripper |
| ของหนัก | meteorite หนักเกินแขนเดียว ต้องจับสองแขน ถ้าปลายแขนห่างกันเกิน 1.2 m จะหลุด |
| ถาดเก็บ (cache) | บนหลังรถที่ (−0.15, 0) ใน `base_link` วางตัวอย่างลงถาดได้ 6 ชิ้น |
| สว่านเจาะ | ใต้ท้องรถ จอดให้ drill site ห่างจากกลางรถไม่เกิน 0.35 m และรถต้องนิ่ง เจาะ 0.04 m/s ร้อนขึ้น 15°C/s เย็นลง 10°C/s เกิน 80°C พัง หลุมต้องลึก 0.3 m จึงได้ core (ออกมาที่ (0.9, 0) หน้ารถ) จึงต้อง cancel พักให้เย็น 2 ครั้งต่อหลุม |
| มุมมอง | parameter `view_zoom`, `view_center_x/y` ภารกิจ 9–10 ซูม 4 เท่า ภารกิจ 11 ซูม 2 เท่า ให้เห็นแขนชัด |

## 5. ROS interface ของ simulator

### ต่อ rover (`/rover1/...`, ทุกชื่อเป็น relative ใต้ namespace ของ rover)

| ชนิด | ชื่อ | type | หมายเหตุ |
|---|---|---|---|
| sub | `cmd_vel` | `geometry_msgs/Twist` | |
| pub | `odom` | `nav_msgs/Odometry` | 50 Hz, frame `map` → `rover1/base_link` |
| pub | `scan` | `sensor_msgs/LaserScan` | 10 Hz, frame `rover1/laser` |
| pub | `camera/detections` | `mars_interfaces/DetectionArray` | 10 Hz |
| pub | `battery` | `sensor_msgs/BatteryState` | 2 Hz, `percentage` 0–1 |
| pub | `bumps` | `std_msgs/Int32` | จำนวนครั้งที่ชน |
| sub | `radio` | `std_msgs/String` | ข้อความขึ้นเป็นบับเบิลเหนือรถ (แทน `say`) |
| srv | `take_photo` | `std_srvs/Trigger` | สำเร็จถ้ามี landmark อยู่ในกล้องและห่างไม่เกิน 3 m, `message` บอกชื่อ |
| srv | `collect` | `std_srvs/Trigger` | เก็บ sample ที่อยู่หน้ารถในระยะ 1.0 m และมุม ±30° |
| srv | `unload` | `std_srvs/Trigger` | ส่งตัวอย่างทั้งหมดให้ lander เมื่ออยู่บน lander |
| pub | `samples_onboard` | `std_msgs/Int32` | จำนวนตัวอย่างบนรถ |
| srv | `teleport` | `mars_interfaces/Teleport` | เครื่องมือ debug ของ sim (เหมือน `set_entity_state` ใน Gazebo) ใช้สอน service ในภารกิจ 3 |
| pub | `joint_states` | `sensor_msgs/JointState` | Part 2 |
| sub | `arm/joint_command` | `sensor_msgs/JointState` | Part 2 ตั้งแค่บางข้อต่อได้ |
| srv | `left_gripper`, `right_gripper` | `std_srvs/SetBool` | Part 2 |
| pub | `left_gripper/holding`, `right_gripper/holding` | `std_msgs/String` | Part 2 |
| action | `drill` | `mars_interfaces/Drill` | Part 2 |

### ส่วนกลาง

| ชนิด | ชื่อ | type | หมายเหตุ |
|---|---|---|---|
| srv | `/spawn_rover` | `mars_interfaces/SpawnRover` | |
| pub | `/tf` | `tf2_msgs/TFMessage` | `map → roverN/base_link → roverN/laser, roverN/drill, roverN/cache, roverN/{left,right}_shoulder → _upper_arm → _forearm → _gripper` |
| pub | `/mars/markers` | `visualization_msgs/MarkerArray` | หิน, lander และวัตถุ สำหรับดูใน RViz |
| sub | `/mission/hud`, `/mission/goals` | `String`, `PoseArray` | mission_control ส่งมาให้วาด |
| srv | `/sim/place_object`, `/sim/clear` | ภายใน | ให้ mission_control จัดฉากเท่านั้น |
| srv | `/sim/screenshot` | `std_srvs/Trigger` | บันทึกภาพหน้าจอ (ใช้ทำภาพประกอบเอกสาร) |
| pub | `/earth/downlink`, `/lander/samples` | `String`, `Int32` | ภาพที่ส่งถึงโลก และจำนวนตัวอย่างใน lander (mission_control อ่านจากที่นี่) |
| pub | `/judge/state` | `String` (JSON) | ค่าจริงของโลก ห้ามผู้เรียนแอบอ่าน (จับได้เหมือนเดิม) |

### mars_interfaces

```
# msg/Detection.msg
string kind        # sample | rock | landmark | beacon | drill_site | core | meteorite
string id
float32 range      # m
float32 bearing    # rad, + = left

# msg/DetectionArray.msg
std_msgs/Header header
Detection[] detections

# srv/SpawnRover.srv
string name
float64 x
float64 y
float64 yaw
---
string name

# srv/Teleport.srv
float64 x
float64 y
float64 yaw
---

# action/Drill.action
float32 depth          # target depth in metres (0.1 - 0.5)
---
bool success
string message
---
float32 depth          # current depth
float32 temperature    # drill bit temperature in °C, over 80 °C the bit breaks
```

### Parameter ของ `mars_sim`

`show_grid`, `cmd_vel_timeout` (1.0), `max_linear_speed`, `max_angular_speed`, `sand_slip` (0.6), `battery_drain` (ค่าคูณ), `arms` (false), `view_zoom`, `view_center_x/y`, `show_sensors`, `seed`, `screenshot_dir`

## 6. ภารกิจ

| # | ภารกิจ | เรียนอะไร | เป้าหมาย |
|---|---|---|---|
| **Part 1** | **The rover** | | |
| 0 | Landing | workspace, build, launch, teleop, remap | ขับลงจาก lander ไปที่ beacon 1 |
| 1 | Telemetry | node, topic, message, `echo/info/hz/pub` | ส่งข้อความวิทยุ, ทวนรหัสจากโลก (`/earth/uplink`), รายงานอัตรา `odom` |
| 2 | Manual Drive | `Twist`, หน่วย, เรเดียน | ผ่าน beacon 1→2→3 ด้วย `ros2 topic pub`, ขับวนรอบ crater หนึ่งรอบ |
| 3 | Mission Control | service, `Trigger` (success/message) | spawn rover `scout`, teleport ไปถ่ายรูป 3 landmark |
| 4 | Survey Square | package, node, publisher, timer | ขับสี่เหลี่ยม 4 m ผ่าน 4 beacon ด้วย node ของตัวเอง |
| 5 | Waypoints | subscriber, `Odometry`, quaternion → yaw, P controller | 5 beacon สุ่มตำแหน่ง มีทรายทำให้ open loop พลาด เวลาได้ดาวคิดจากความยาวเส้นทางของรอบนั้น |
| 6 | Sample Hunter | กล้อง + `LaserScan`, service client, `call_async` | เก็บ sample 5 ชิ้น ชนหินได้ดาวสูงสุด 2 ดวง หินไม่ขวางเส้นทางลาดตระเวน (`PATROL`) จึงใช้วิธีหลบแบบง่ายได้ |
| 7 | Rover Fleet | namespace, parameter, launch | 2 rover รันโค้ดเดียวกัน, เปลี่ยน `max_speed` สด, รวม 10 ชิ้น |
| 8 | **Boss: Power Crisis** | state machine, แบตเตอรี่ | ส่งตัวอย่าง 6 ชิ้นเข้า lander โดยแบตไม่หมด เริ่มที่ 35% กินแบตเร็ว 4 เท่า ต้องกลับไปชาร์จอย่างน้อย 1 รอบ |
| **Part 2** | **The arm** | | |
| 9 | Arm Check | `JointState`, gripper `SetBool`, forward kinematics | จอดนิ่ง แตะเป้าซ้ายด้วยแขนซ้าย เป้าขวาด้วยแขนขวา แล้วหยิบหิน |
| 10 | Frames | **tf2**: `tf2_echo`, `tf_buffer.transform()`, RViz, IK | rover จอดหันมุมสุ่ม แตะเป้า 6 จุด (ให้มาใน frame `map`) แปลงเข้า frame ไหล่ด้วย tf2 แล้วทำ IK |
| 11 | Drill & Stow | **action client**: goal, feedback, cancel, result + pick & place | จอดคร่อมจุดเจาะ เจาะ 3 จุดโดยหยุดก่อนสว่านร้อนเกิน แล้วใช้แขนหยิบ core ใส่ถาด |
| 12 | **Boss: Meteorite Recovery** | ทุกอย่างรวมกัน: ขับ, สองแขนช่วยกัน, แบต | ใช้สองแขนยก meteorite 2 ก้อนกลับไปวางที่ lander เริ่มแบต 60% กินเร็ว 3 เท่า หินไม่ขวางเส้นตรง lander↔meteorite ตำแหน่งปัจจุบันของ meteorite อยู่บน `/mission/items` |

ทุกภารกิจมีโครงเดิม: วัตถุประสงค์บนแผงขวา, ดาวตามเวลา, จับ teleop/`topic pub`/teleport/การแอบอ่าน `/judge/objects` ภารกิจ 8 และ 12 เป็น skeleton พร้อม TODO เหมือน boss เดิม

**ต่อยอดหลังคอร์ส (CONCEPTS "Not covered yet"):** custom interface ของตัวเอง, เขียน action server เอง (เช่น `navigate_to`), `ros2 bag` บันทึกภารกิจแล้วเล่นซ้ำ, odom drift กับ frame `map → odom` (ยังไม่มีใน sim), URDF + `robot_state_publisher`, C++, Nav2

## 7. mission_control

ใช้กลไกเดียวกับ `quest_master`:
- สั่ง sim ล้างและจัดฉาก
- ตรวจ objective ที่ 10 Hz จาก topic สาธารณะ
- ส่ง `/mission/hud` และ `/mission/goals`
- ตรวจ graph หาผู้ publish `cmd_vel` และ `arm/joint_command`
- เก็บคะแนนดีที่สุด (`ros2 run mission_control progress`)

สิ่งที่เพิ่ม:
- ภารกิจล้มเหลวได้ เมื่อแบตหมด หรือสว่านพังในภารกิจ 11–12 แผงจะบอกเหตุผลและวิธีเริ่มใหม่
- ตรวจ teleport จาก service call count ที่ sim รายงาน แทนการเดาจากระยะกระโดด

## 8. Dependencies

ทุกอย่างอยู่ใน `ros-<distro>-ros-base` ยกเว้นที่ระบุ
- `rclpy`, `std_msgs`, `std_srvs`, `geometry_msgs`, `nav_msgs`, `sensor_msgs`, `tf2_ros`, `visualization_msgs`
- `python3-pygame`, `python3-numpy`
- `ros-<distro>-teleop-twist-keyboard`
- `rviz2` (ไม่บังคับ ใช้ในภารกิจ 10 ถ้าติดตั้ง desktop)

รองรับ Jazzy (แนะนำ) และ Humble ทดสอบใน Docker เหมือนเดิม

## 9. Repo และขั้นตอน

**Solutions:** อยู่ใน `solutions/` ที่ gitignore ไว้

**Layout:** `src/mars_sim`, `src/mars_interfaces`, `src/mission_control`, `missions/00-landing.md` …, `slides/`, `docs/images/`

**ลำดับงาน** (จบแต่ละเฟสแล้วรีวิวก่อนไปต่อ):
1. `mars_interfaces` + `mars_sim` (ขับ, odom, scan, กล้อง, แบต, หิน, ทราย, TF) + `mission_control` + ภารกิจ 0–4 พร้อมทดสอบ headless
2. ภารกิจ 5–8 + เฉลย (local)
3. สองแขน, tf2, drill action, meteorite + ภารกิจ 9–12
4. เอกสาร: README, TEACHER, ARCHITECTURE, CONCEPTS, CHECKLIST, CHEATSHEET, slides, system maps และภาพหน้าจอ

**License:** simulator ใหม่เขียนเองทั้งหมด จึงเลือก license ได้ เสนอ Apache-2.0 (มาตรฐานของ ROS 2)
