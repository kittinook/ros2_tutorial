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

# The GPL3 license is a widely used free software license that allows 
# users to run, study, share, and modify software. It requires that 
# any derivative works or modifications made to the software be 
# licensed under the GPL3 and that the source code be made available 
# to anyone who receives the software.


# other libraries
import os
import math
import random
import time
import abc
from functools import partial
from typing import Dict, List
import pygame

# package module
from turtlesim_plus.entity import (
    Entity, PhysicsEntity, GraphicsEntity, Pizza, Parcel, DropZone, Turtle,
    TurtleCommandInterface,TurtleScannerInterface,TurtleEatInterface,TurtleDeliveryInterface,
    Simulator
)
from turtlesim_plus.world import WORLD_SIZE, world_to_screen, screen_to_world, DROPOFF_ZONE_POSE, DROPOFF_ZONE_RADIUS
from turtlesim_plus import ui
from turtlesim_plus.arms import DualArms, Crate, JOINT_NAMES, panel_text

# RCLPY libraries, classes, functions
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.action.server import ServerGoalHandle

# ROS Packages
from std_msgs.msg import Int64, Bool, String
from std_srvs.srv import Empty, SetBool
from sensor_msgs.msg import JointState
from turtlesim.msg import Pose
from turtlesim.srv import Spawn, Kill, SetPen, TeleportAbsolute, TeleportRelative
from geometry_msgs.msg import Twist, Point, PoseArray
from turtlesim_plus_interfaces.msg import ScannerData, ScannerDataArray, WorldObject, WorldObjectArray
from turtlesim_plus_interfaces.srv import GivePosition
from turtlesim_plus_interfaces.action import GetData

class ROS2Plugin(abc.ABC):
    def __init__(self,node:Node):
        self.node = node
class MouseROS2Plugin(ROS2Plugin):
    def __init__(self,node:Node):
        super().__init__(node=node)
        self.mouse_pub = self.node.create_publisher(Point,'mouse_position',10)
        self.node.simulator.mouse_callback = self.mouse_callback
    def mouse_callback(self,pos):
        msg = Point()
        msg.x,msg.y = screen_to_world(pos[0],pos[1])
        self.mouse_pub.publish(msg)
class TurtleCommandROS2Plugin(TurtleCommandInterface,ROS2Plugin):
    def __init__(self, turtle: Turtle,node: Node,image):
        TurtleCommandInterface.__init__(self,turtle=turtle)
        ROS2Plugin.__init__(self,node=node)
        self.cmd_vel_pub = self.node.create_publisher(Pose,self.turtle.name+'/pose',10)
        self.sub = self.node.create_subscription(Twist,self.turtle.name+'/cmd_vel',self.cmd_vel_sub_callback,10)
        self.stop_service = self.node.create_service(Empty,self.turtle.name+'/stop',self.stop_srv_callback)
        self.set_pen_service = self.node.create_service(SetPen,self.turtle.name+'/set_pen',self.set_pen_srv_callback)
        self.teleport_absolute_service = self.node.create_service(TeleportAbsolute,self.turtle.name+'/teleport_absolute',self.teleport_absolute_srv_callback)
        self.teleport_relative_service = self.node.create_service(TeleportRelative,self.turtle.name+'/teleport_relative',self.teleport_relative_srv_callback)
        self.say_sub = self.node.create_subscription(String,self.turtle.name+'/say',self.say_sub_callback,10)
        self.image = image
        self.speech = ''
        self.speech_until = 0.0
        self.last_command_time = 0.0
    SPEECH_DURATION = 5.0  # seconds a /say message stays on screen
    def say_sub_callback(self,msg:String):
        self.speech = msg.data
        self.speech_until = time.monotonic()+self.SPEECH_DURATION
        self.node.get_logger().info(f'{self.turtle.name} says: {msg.data}')
    def cmd_vel_sub_callback(self,msg:Twist):
        self.command_velocity = [msg.linear.x,msg.angular.z]
        self.last_command_time = time.monotonic()
    def stop_srv_callback(self,request:Empty.Request,response:Empty.Response):
        self.command_velocity = [0.0,0.0]
        return response
    def set_pen_srv_callback(self,request:SetPen.Request,response:SetPen.Response):
        self.turtle.set_pen(r=request.r,g=request.g,b=request.b,width=request.width,off=bool(request.off))
        return response
    def teleport_absolute_srv_callback(self,request:TeleportAbsolute.Request,response:TeleportAbsolute.Response):
        self.turtle.teleport(x=request.x,y=request.y,theta=request.theta)
        self.set_state(self.turtle.state)
        self.set_pose(self.turtle.state)
        return response
    def teleport_relative_srv_callback(self,request:TeleportRelative.Request,response:TeleportRelative.Response):
        theta = self.turtle.pose[2]
        x = self.turtle.pose[0] + request.linear*math.cos(theta)
        y = self.turtle.pose[1] + request.linear*math.sin(theta)
        self.turtle.teleport(x=x,y=y,theta=theta+request.angular)
        self.set_state(self.turtle.state)
        self.set_pose(self.turtle.state)
        return response
    def update(self, dt: float = 0.1, *args, **kwargs):
        # Like stock turtlesim: stop if no cmd_vel arrived for cmd_vel_timeout seconds
        # (0 disables it), so a single teleop keypress doesn't send the turtle off forever.
        timeout = self.node.cmd_vel_timeout
        if timeout > 0 and time.monotonic()-self.last_command_time > timeout:
            self.command_velocity = [0.0,0.0]
        TurtleCommandInterface.update(self, dt, *args, **kwargs)
        self.set_state(self.turtle.state)
        self.set_pose(self.turtle.state)
        msg = Pose()
        msg.x = self.state[0]
        msg.y = self.state[1]
        msg.theta = self.state[2]
        msg.linear_velocity = float(self.command_velocity[0])
        msg.angular_velocity = float(self.command_velocity[1])
        self.cmd_vel_pub.publish(msg=msg)
    def __del__(self):
        self.node.destroy_publisher(publisher=self.cmd_vel_pub)
        self.node.destroy_subscription(subscription=self.sub)
        self.node.destroy_service(service=self.stop_service)
        self.node.destroy_service(service=self.set_pen_service)
        self.node.destroy_service(service=self.teleport_absolute_service)
        self.node.destroy_service(service=self.teleport_relative_service)
        self.node.destroy_subscription(subscription=self.say_sub)
class TurtleScannerROS2Plugin(TurtleScannerInterface,ROS2Plugin):
    def __init__(self, turtle:Turtle,node:Node,scanner_radius:float=4.0,scanner_angle_range:float=math.pi/3):
        TurtleScannerInterface.__init__(self,turtle=turtle,scanner_radius=scanner_radius,scanner_angle_range=scanner_angle_range)
        ROS2Plugin.__init__(self,node=node)
        self.scanner_pub = self.node.create_publisher(ScannerDataArray,self.turtle.name+'/scan',10)
        self.action_server = ActionServer(self.node,GetData,self.turtle.name+'/detect_pizza',self.execute_callback)
    def execute_callback(self,goal_handle:ServerGoalHandle):
        result = GetData.Result()
        if len(self.scanner_output)>0:
            result.is_data = True
            msg = ScannerDataArray()
            for data in self.scanner_output:
                scanner_data = ScannerData()
                if str(data.type.__name__)=='Pizza':
                    scanner_data.type = 'Pizza'
                    scanner_data.angle = data.angle
                    scanner_data.distance = data.distance
                    msg.data.append(scanner_data)
            result.data = msg
            goal_handle.succeed()
        else:
            result.is_data = False
            goal_handle.abort()
        return result
    def update(self, dt: float = 0.1, entity_list:Dict[str,Entity] = {}, *args, **kwargs):
        TurtleScannerInterface.update(self,dt=dt,entity_list=entity_list)
        self.set_state(self.turtle.state)
        # Published every tick, even when nothing is in the cone (empty list) --
        # the upstream version only published on detections, which makes "I see
        # nothing" indistinguishable from "the sensor is dead" for beginners.
        msg = ScannerDataArray()
        for data in self.scanner_output:
            scanner_data = ScannerData()
            if str(data.type.__name__).startswith('Turtle'):
                scanner_data.type = 'Turtle'
            else:
                scanner_data.type = data.type.__name__
            scanner_data.angle = data.angle
            scanner_data.distance = data.distance
            msg.data.append(scanner_data)
        self.scanner_pub.publish(msg)
    def __del__(self):
        self.node.destroy_publisher(publisher=self.scanner_pub)
        # __del__ runs twice for a removed turtle (explicitly, then again on GC);
        # unlike destroy_publisher, ActionServer.destroy() raises the second time
        if self.action_server is not None:
            self.action_server.destroy()
            self.action_server = None
class TurtleEatROS2Plugin(TurtleEatInterface,ROS2Plugin):
    def __init__(self, turtle:Turtle,node:Node,eat_radius:float=2.0,eat_angle_range:float=math.pi/3):
        TurtleEatInterface.__init__(self,turtle=turtle,eat_radius=eat_radius,eat_angle_range=eat_angle_range)
        ROS2Plugin.__init__(self,node=node)
        self.pizza_count = 0
        self.pizza_count_publisher = self.node.create_publisher(Int64,self.turtle.name+'/pizza_count',10)
        self.eat_service = self.node.create_service(Empty,self.turtle.name+'/eat',self.eat_srv_callback)
    def eat_srv_callback(self,request:Empty.Request,response:Empty.Response):
        if len(self.edibles)>0:
            self.pizza_count+=1
            edible = self.edibles.pop(0)
            del self.node.simulator.entity_list[edible.name]
            del self.node.simulator.gui.entity_list[edible.name]
        return response
    def update(self, dt: float = 0.1, entity_list:Dict[str,Entity] = {}, *args, **kwargs):
        TurtleEatInterface.update(self,dt=dt,entity_list=entity_list)
        self.set_state(self.turtle.state)
        msg = Int64()
        msg.data = self.pizza_count
        self.pizza_count_publisher.publish(msg)
    def __del__(self):
        self.node.destroy_publisher(publisher=self.pizza_count_publisher)
        self.node.destroy_service(service=self.eat_service)
class TurtleDeliveryROS2Plugin(TurtleDeliveryInterface,ROS2Plugin):
    def __init__(self, turtle:Turtle,node:Node,pickup_radius:float=2.0,pickup_angle_range:float=math.pi/3):
        TurtleDeliveryInterface.__init__(self,turtle=turtle,pickup_radius=pickup_radius,pickup_angle_range=pickup_angle_range)
        ROS2Plugin.__init__(self,node=node)
        self.parcel_count = 0
        self.carrying_parcel = False
        self.parcel_count_publisher = self.node.create_publisher(Int64,self.turtle.name+'/parcel_count',10)
        self.carrying_parcel_publisher = self.node.create_publisher(Bool,self.turtle.name+'/carrying_parcel',10)
        self.pickup_service = self.node.create_service(Empty,self.turtle.name+'/pickup',self.pickup_srv_callback)
        self.dropoff_service = self.node.create_service(Empty,self.turtle.name+'/dropoff',self.dropoff_srv_callback)
    def pickup_srv_callback(self,request:Empty.Request,response:Empty.Response):
        if not self.carrying_parcel and len(self.nearby_parcels)>0:
            parcel = self.nearby_parcels[0]
            del self.node.simulator.entity_list[parcel.name]
            del self.node.simulator.gui.entity_list[parcel.name]
            self.carrying_parcel = True
        return response
    def dropoff_srv_callback(self,request:Empty.Request,response:Empty.Response):
        if self.carrying_parcel:
            dx = self.pose[0]-DROPOFF_ZONE_POSE[0]
            dy = self.pose[1]-DROPOFF_ZONE_POSE[1]
            if math.sqrt(dx*dx+dy*dy) <= DROPOFF_ZONE_RADIUS:
                self.parcel_count += 1
                self.carrying_parcel = False
        return response
    def update(self, dt: float = 0.1, entity_list:Dict[str,Entity] = {}, *args, **kwargs):
        TurtleDeliveryInterface.update(self,dt=dt,entity_list=entity_list)
        self.set_state(self.turtle.state)
        count_msg = Int64()
        count_msg.data = self.parcel_count
        self.parcel_count_publisher.publish(count_msg)
        carrying_msg = Bool()
        carrying_msg.data = self.carrying_parcel
        self.carrying_parcel_publisher.publish(carrying_msg)
    def __del__(self):
        self.node.destroy_publisher(publisher=self.parcel_count_publisher)
        self.node.destroy_publisher(publisher=self.carrying_parcel_publisher)
        self.node.destroy_service(service=self.pickup_service)
        self.node.destroy_service(service=self.dropoff_service)
class TurtleArmsROS2Plugin(ROS2Plugin):
    """Two arms + grippers (see arms.py) exposed as standard ROS 2 interfaces:
    joint_command / joint_states (sensor_msgs/JointState), <side>_gripper (std_srvs/SetBool),
    <side>_arm/tip (geometry_msgs/Point) and <side>_gripper/holding (std_msgs/String)."""
    def __init__(self, turtle: Turtle, node: Node):
        ROS2Plugin.__init__(self,node=node)
        self.turtle = turtle
        self.arms = DualArms(turtle.name)
        name = turtle.name
        self.joint_state_pub = node.create_publisher(JointState,name+'/joint_states',10)
        self.joint_command_sub = node.create_subscription(JointState,name+'/joint_command',self.joint_command_callback,10)
        self.tip_pubs = {side:node.create_publisher(Point,f'{name}/{side}_arm/tip',10) for side in ('left','right')}
        self.holding_pubs = {side:node.create_publisher(String,f'{name}/{side}_gripper/holding',10) for side in ('left','right')}
        self.gripper_services = {side:node.create_service(SetBool,f'{name}/{side}_gripper',partial(self.gripper_callback,side))
                                 for side in ('left','right')}
    def joint_command_callback(self,msg:JointState):
        if len(msg.position) < len(msg.name):
            self.node.get_logger().warning(f'{self.turtle.name}/joint_command: every name needs a position',
                                           throttle_duration_sec=2.0)
        unknown = self.arms.set_targets(list(msg.name),list(msg.position))
        if unknown:
            self.node.get_logger().warning(f'{self.turtle.name}/joint_command: unknown joint(s) {unknown}, '
                                           f'expected {JOINT_NAMES}',throttle_duration_sec=2.0)
    def gripper_callback(self,side:str,request:SetBool.Request,response:SetBool.Response):
        if request.data:
            response.success,response.message = self.arms.grasp(side,self.turtle.pose,self.node.simulator.entity_list)
        else:
            response.success,response.message = self.arms.release(side)
        return response
    def update(self, dt: float, entity_list: Dict[str,Entity]):
        self.arms.update(dt,self.node.arm_joint_speed,self.turtle.pose,entity_list,log=self.node.get_logger().info)
        msg = JointState()
        msg.header.stamp = self.node.get_clock().now().to_msg()
        msg.name = list(JOINT_NAMES)
        msg.position = [float(q) for q in self.arms.joint_positions()]
        msg.velocity = [float(v) for v in self.arms.joint_velocities()]
        self.joint_state_pub.publish(msg)
        for side,arm in self.arms.arms.items():
            x,y = arm.tip_world(self.turtle.pose)
            self.tip_pubs[side].publish(Point(x=float(x),y=float(y),z=0.0))
            self.holding_pubs[side].publish(String(data=self.arms.holding(side)))
    def __del__(self):
        self.arms.release_all()
        self.node.destroy_publisher(self.joint_state_pub)
        self.node.destroy_subscription(self.joint_command_sub)
        for pub in list(self.tip_pubs.values())+list(self.holding_pubs.values()):
            self.node.destroy_publisher(pub)
        for srv in self.gripper_services.values():
            self.node.destroy_service(srv)

class TurtlePlugin(PhysicsEntity,GraphicsEntity,ROS2Plugin):
    """Owns command/scanner/eat as components instead of inheriting from all three.

    Replaces the old TurtleCommandScannerEatROS2Plugin, which triple-inherited
    TurtleScannerROS2Plugin/TurtleCommandROS2Plugin/TurtleEatROS2Plugin and had to
    manually chain __init__/update/render/__del__ across all three in a specific
    order. That also caused the turtle sprite to be blit'd three times per frame
    (each parent's render() independently re-rendered self.turtle). Here each
    component is a separate object and the turtle sprite is drawn exactly once.
    """
    def __init__(self, turtle: Turtle, node: Node, image,
                 scanner_radius: float = 4.0, scanner_angle_range: float = math.pi/3,
                 eat_radius: float = 2.0, eat_angle_range: float = math.pi/3,
                 pickup_radius: float = 2.0, pickup_angle_range: float = math.pi/3):
        PhysicsEntity.__init__(self,name=turtle.name)
        ROS2Plugin.__init__(self,node=node)
        self.turtle = turtle
        self.image = image
        self.pose = turtle.pose
        self.state = turtle.state
        self.command = TurtleCommandROS2Plugin(turtle=turtle,node=node,image=image)
        self.scanner = TurtleScannerROS2Plugin(turtle=turtle,node=node,scanner_radius=scanner_radius,scanner_angle_range=scanner_angle_range)
        self.eat = TurtleEatROS2Plugin(turtle=turtle,node=node,eat_radius=eat_radius,eat_angle_range=eat_angle_range)
        self.delivery = TurtleDeliveryROS2Plugin(turtle=turtle,node=node,pickup_radius=pickup_radius,pickup_angle_range=pickup_angle_range)
        # entity_list (under this ROS2 layer) holds TurtlePlugin wrappers, not raw
        # Turtle instances -- TurtleScannerInterface registered Turtle as a
        # detection type at the entity.py layer, which never matches here, so
        # register the actual wrapper type too or turtle-to-turtle scanning silently
        # detects nothing.
        self.scanner.scanner.add_detection_type(TurtlePlugin)
        self.scanner.scanner.add_detection_type(Crate)
        self.arms = TurtleArmsROS2Plugin(turtle=turtle,node=node) if node.arms_enabled else None
    def set_pose(self, pose: List[float]):
        GraphicsEntity.set_pose(self,pose=pose)
        self.turtle.set_pose(pose=pose)
    def set_state(self, state: List[float]):
        PhysicsEntity.set_state(self,state=state)
        self.turtle.set_state(state=state)
    def update(self, dt: float = 0.1, entity_list: Dict[str,Entity] = {}, *args, **kwargs):
        self.command.update(dt=dt)
        # sync the shared turtle's fresh pose into the scanner/eat components
        # before they measure against it (they each track their own pose/state).
        self.scanner.pose = self.turtle.pose
        self.scanner.state = self.turtle.state
        self.scanner.update(dt=dt,entity_list=entity_list)
        self.eat.pose = self.turtle.pose
        self.eat.state = self.turtle.state
        self.eat.update(dt=dt,entity_list=entity_list)
        self.delivery.pose = self.turtle.pose
        self.delivery.state = self.turtle.state
        self.delivery.update(dt=dt,entity_list=entity_list)
        if self.arms is not None:
            self.arms.update(dt=dt,entity_list=entity_list)
        self.pose = self.turtle.pose
        self.state = self.turtle.state
    carry_icon = None  # small parcel sprite drawn on the turtle's back while carrying
    def render_sensors(self, screen):
        # Drawn in a background pass (before pizzas/parcels) so the translucent
        # cones never hide the objects they are detecting. Pickup shares the eat
        # cone's default size, so it's an outline to keep the green eat cone visible.
        self.scanner.scanner.render(screen,pose=self.turtle.pose)
        self.eat.eat_range.render(screen,pose=self.turtle.pose)
        self.delivery.pickup_range.render(screen,pose=self.turtle.pose,width=1)
    def render(self, screen):
        self.turtle.render(screen)
        if self.arms is not None:
            self.arms.arms.render(screen,self.turtle.pose)
        sx,sy = world_to_screen(self.turtle.pose[0],self.turtle.pose[1])
        ui.draw_label(screen,self.name,(sx,sy+30),color=ui.GREY,size=12)
        if self.delivery.carrying_parcel and self.carry_icon is not None:
            screen.blit(self.carry_icon,(sx-self.carry_icon.get_width()/2,sy-self.carry_icon.get_height()/2))
        if self.command.speech and time.monotonic() < self.command.speech_until:
            ui.draw_speech_bubble(screen,self.command.speech,(sx,sy))
    def __del__(self):
        self.command.__del__()
        self.scanner.__del__()
        self.eat.__del__()
        self.delivery.__del__()
        if self.arms is not None:
            self.arms.__del__()
class TurtlesimPlusNode(Node):
    def __init__(self):
        super().__init__(node_name='turtlesim_plus')
        self.declare_parameter('time_step',0.01)
        self.declare_parameter('scanner_radius',4.0)
        self.declare_parameter('scanner_angle_range',math.pi/3)
        self.declare_parameter('eat_radius',2.0)
        self.declare_parameter('eat_angle_range',math.pi/3)
        self.declare_parameter('pickup_radius',2.0)
        self.declare_parameter('pickup_angle_range',math.pi/3)
        self.declare_parameter('show_grid',True)
        self.declare_parameter('cmd_vel_timeout',1.0)
        self.declare_parameter('arms',False)
        self.declare_parameter('arm_joint_speed',2.0)
        self.arms_enabled = self.get_parameter('arms').value
        self.arm_joint_speed = self.get_parameter('arm_joint_speed').value
        self.cmd_vel_timeout = self.get_parameter('cmd_vel_timeout').value
        time_step = self.get_parameter('time_step').value
        self.scanner_radius = self.get_parameter('scanner_radius').value
        self.scanner_angle_range = self.get_parameter('scanner_angle_range').value
        self.eat_radius = self.get_parameter('eat_radius').value
        self.eat_angle_range = self.get_parameter('eat_angle_range').value
        self.pickup_radius = self.get_parameter('pickup_radius').value
        self.pickup_angle_range = self.get_parameter('pickup_angle_range').value
        self.simulator = Simulator(time_step=time_step)
        self.simulator.gui.register_render_order(DropZone)
        self.simulator.gui.register_render_order(Crate)
        self.simulator.gui.register_render_order(Pizza)
        self.simulator.gui.register_render_order(Parcel)
        self.simulator.gui.register_render_order(TurtlePlugin)
        drop_zone = DropZone(name='dropoff_zone',pose=[DROPOFF_ZONE_POSE[0],DROPOFF_ZONE_POSE[1],0.0],radius=DROPOFF_ZONE_RADIUS)
        self.simulator.add_entity(entity=drop_zone)
        self.mouse_plugin = MouseROS2Plugin(self)
        # Teaching overlays: anything may publish a HUD text / goal flags to draw
        # (turtle_quest's mission node does), the simulator just renders them.
        self.hud_text = ''
        self.goals = []
        self.create_subscription(String,'hud',self.hud_sub_callback,10)
        self.create_subscription(PoseArray,'mission/goals',self.goals_sub_callback,10)
        if self.get_parameter('show_grid').value:
            self.simulator.gui.background_renderers.append(ui.draw_grid)
        self.simulator.gui.background_renderers.append(self.render_sensors)
        self.simulator.gui.overlay_renderers.append(self.render_goals)
        self.simulator.gui.overlay_renderers.append(self.render_panel)
        parcel_img = pygame.image.load(os.path.join(self.simulator.gui.image_dir,'object','parcel.png')).convert_alpha()
        icon = Parcel(name='_carry_icon',pose=[0.0,0.0,0.0])
        icon.TARGET_SIZE = 22
        icon.set_graphics(graphics=parcel_img)
        TurtlePlugin.carry_icon = icon.graphics
        self.create_timer(time_step,self.timer_callback)
        self.spawn_turtle_service = self.create_service(Spawn,'spawn_turtle',self.spawn_turtle_srv_callback)
        self.remove_turtle_service = self.create_service(Kill,'remove_turtle',self.remove_turtle_srv_callback)
        self.spawn_pizza_service = self.create_service(GivePosition,'spawn_pizza',self.spawn_pizza_srv_callback)
        self.spawn_parcel_service = self.create_service(GivePosition,'spawn_parcel',self.spawn_parcel_srv_callback)
        self.clear_service = self.create_service(Empty,'clear',self.clear_srv_callback)
        self.clear_objects_service = self.create_service(Empty,'clear_objects',self.clear_objects_srv_callback)
        self.spawn_crate_service = self.create_service(GivePosition,'spawn_crate',self.spawn_crate_srv_callback)
        # The judge's view of the world (every object, where it is, who holds it).
        # Meant for referees like turtle_quest's quest_master, not for robots.
        self.judge_pub = self.create_publisher(WorldObjectArray,'judge/objects',10)
        self.create_timer(0.1,self.publish_judge_objects)
        prompt = """

        Welcome to Turtlesim+!!

        You can call the following services to interact with 'the simulator':
        /spawn_turtle,/remove_turtle,/spawn_pizza,/spawn_parcel,/spawn_crate,/clear,/clear_objects

        "Once you spawn at least 1 turtle, you can read from the following topics:
        /[name]/pose,/[name]/scan,/[name]/pizza_count,/[name]/parcel_count,/[name]/carrying_parcel

        You can also publish to '/[name]/cmd_vel' and '/[name]/say'.

        You can also call the following turtle's services.
        /[name]/eat,/[name]/stop,/[name]/pickup,/[name]/dropoff

        A parcel must be dropped off near the far corner of the world.

        With arms enabled (parameter arms:=true) each turtle also has:
        /[name]/joint_command, /[name]/joint_states, /[name]/left_gripper, /[name]/right_gripper,
        /[name]/left_arm/tip, /[name]/right_arm/tip, /[name]/left_gripper/holding, /[name]/right_gripper/holding

        """
        self.get_logger().info(prompt)
        
        request = Spawn.Request()
        request.name = 'turtle1'
        request.x = float('nan')
        request.y = float('nan')
        request.theta = float('nan')
        response = Spawn.Response()
        self.spawn_turtle_srv_callback(request,response)

    def hud_sub_callback(self,msg:String):
        self.hud_text = msg.data
    def goals_sub_callback(self,msg:PoseArray):
        # position.z carries the goal's radius (0 -> default 0.5)
        self.goals = [(p.position.x,p.position.y,p.position.z if p.position.z>0 else 0.5) for p in msg.poses]
    def render_sensors(self,screen):
        for entity in self.simulator.entity_list.values():
            if isinstance(entity,TurtlePlugin):
                entity.render_sensors(screen)
    def render_goals(self,screen):
        # drawn last-to-first so the next goal (index 1) ends up on top
        for i in reversed(range(len(self.goals))):
            x,y,r = self.goals[i]
            ui.draw_goal(screen,i+1,x,y,r,is_next=(i==0))
    def render_panel(self,screen):
        turtles = []
        for entity in self.simulator.entity_list.values():
            if isinstance(entity,TurtlePlugin):
                turtles.append({'name':entity.name,'x':entity.turtle.pose[0],'y':entity.turtle.pose[1],
                                'theta':entity.turtle.pose[2],'pizza':entity.eat.pizza_count,
                                'parcel':entity.delivery.parcel_count,'carrying':entity.delivery.carrying_parcel,
                                'arms':panel_text(entity.arms.arms) if entity.arms is not None else ''})
        ui.draw_panel(screen,self.hud_text,turtles)
    def clear_objects_srv_callback(self,request:Empty.Request,response:Empty.Response):
        """Remove every pizza, parcel and crate from the world (turtles stay)."""
        for name,entity in list(self.simulator.entity_list.items()):
            if isinstance(entity,(Pizza,Parcel,Crate)):
                self.simulator.remove_entity(entity=entity)
        return response
    def clear_srv_callback(self,request:Empty.Request,response:Empty.Response):
        for entity in self.simulator.entity_list.values():
            if isinstance(entity,TurtlePlugin):
                entity.turtle.clear_trail()
        return response

    def spawn_turtle_srv_callback(self,request:Spawn.Request,response:Spawn.Response):
        init_pose = [WORLD_SIZE/2,WORLD_SIZE/2,0.0]
        if not request.name:
            flag = True
            name = 'turtle1'
            idx = 0
            while name in self.simulator.entity_list.keys():
                idx += 1
                name = 'turtle'+str(idx)
        else:
            flag = False
            base_name = request.name
            name = base_name
            idx = 0
            while name in self.simulator.entity_list.keys():
                idx += 1
                name = f'{base_name}_{idx}'
        if flag:
            self.get_logger().info(f'Name is not given. Use {name} instead.')
        elif name != request.name:
            self.get_logger().info(f'The name {request.name} already exists in Turtlesim Plus. Use {name} instead.')
        if math.isnan(request.x):
            x = init_pose[0]
        else:
            x = request.x
        if math.isnan(request.y):
            y = init_pose[1]
        else:
            y = request.y
        if math.isnan(request.theta):
            theta = init_pose[2]
        else:
            theta = request.theta

        image = random.choice(self.simulator.gui.available_images)
        self.simulator.gui.available_images.remove(image)       
        turtle = Turtle(name=name,init_pose=[x,y,theta])
        # load graphics when added
        graphics = pygame.image.load(os.path.join(self.simulator.gui.image_dir,'turtle',image)).convert_alpha()
        turtle.set_graphics(graphics=graphics)
        ros2_turtle = TurtlePlugin(turtle=turtle,node=self,image=image,
                                    scanner_radius=self.scanner_radius,scanner_angle_range=self.scanner_angle_range,
                                    eat_radius=self.eat_radius,eat_angle_range=self.eat_angle_range,
                                    pickup_radius=self.pickup_radius,pickup_angle_range=self.pickup_angle_range)
        self.simulator.add_entity(entity=ros2_turtle)
        response.name = name
        return response
    def remove_turtle_srv_callback(self,request:Kill.Request,response:Kill.Response):
        if not request.name:
            self.get_logger().warning('No name is given. No turtle is removed.')
        else:
            if request.name in self.simulator.entity_list.keys():
                entity = self.simulator.entity_list[request.name]
                if isinstance(entity,TurtlePlugin):
                    self.simulator.remove_entity(entity=entity)
                    self.simulator.engine.remove_entity(entity=entity)
                    self.simulator.gui.available_images.append(entity.image)
                    entity.__del__()
                    self.get_logger().warning(f'Successfully remove {request.name}')
            else:
                self.get_logger().warning(f'No turtle with the name {request.name}')
        return response
    def spawn_pizza_srv_callback(self,request:GivePosition.Request,response:GivePosition.Response):
        idx = 0
        name = 'pizza'+str(idx)
        while name in self.simulator.entity_list.keys():
            idx += 1
            name = 'pizza'+str(idx)
        if math.isnan(request.x):
            x = random.uniform(0,WORLD_SIZE)
        else:
            x = request.x
        if math.isnan(request.y):
            y = random.uniform(0,WORLD_SIZE)
        else:
            y = request.y
        # load graphics when added
        graphics = pygame.image.load(os.path.join(self.simulator.gui.image_dir,'object','pizza.png')).convert_alpha()
        pizza = Pizza(name=name,pose=[x,y,0.0])
        pizza.set_graphics(graphics=graphics)
        self.simulator.add_entity(entity=pizza)
        return response
    def spawn_parcel_srv_callback(self,request:GivePosition.Request,response:GivePosition.Response):
        idx = 0
        name = 'parcel'+str(idx)
        while name in self.simulator.entity_list.keys():
            idx += 1
            name = 'parcel'+str(idx)
        if math.isnan(request.x):
            x = random.uniform(0,WORLD_SIZE)
        else:
            x = request.x
        if math.isnan(request.y):
            y = random.uniform(0,WORLD_SIZE)
        else:
            y = request.y
        # load graphics when added
        graphics = pygame.image.load(os.path.join(self.simulator.gui.image_dir,'object','parcel.png')).convert_alpha()
        parcel = Parcel(name=name,pose=[x,y,0.0])
        parcel.set_graphics(graphics=graphics)
        self.simulator.add_entity(entity=parcel)
        return response

    def spawn_crate_srv_callback(self,request:GivePosition.Request,response:GivePosition.Response):
        idx = 0
        while f'crate{idx}' in self.simulator.entity_list:
            idx += 1
        x = random.uniform(1.0,WORLD_SIZE-1.0) if math.isnan(request.x) else request.x
        y = random.uniform(1.0,WORLD_SIZE-1.0) if math.isnan(request.y) else request.y
        self.simulator.add_entity(entity=Crate(name=f'crate{idx}',pose=[x,y,0.0]))
        return response
    def publish_judge_objects(self):
        msg = WorldObjectArray()
        for entity in self.simulator.entity_list.values():
            if isinstance(entity,(Pizza,Parcel,Crate)):
                held_by = ','.join(entity.holders) if isinstance(entity,Crate) else getattr(entity,'held_by','')
                msg.objects.append(WorldObject(name=entity.name,type=type(entity).__name__,
                                               x=float(entity.pose[0]),y=float(entity.pose[1]),held_by=held_by))
        self.judge_pub.publish(msg)
    def timer_callback(self):
        self.simulator.step()
