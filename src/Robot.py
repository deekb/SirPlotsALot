from VEXLib.Algorithms.PID import PIDController
from VEXLib.Math.MathUtil import MathUtil
from VEXLib.Robot.TelemteryRobot import TelemetryRobot
from VEXLib.Util import time
from vex import *
from dxf_parser import DXFParser


class Robot(TelemetryRobot):
    def __init__(self, brain):
        super().__init__(brain)
        self.tool_position = (0, 0)
        self.y_track_length_in = 9.25
        self.x_track_length_in = 9.0
        self.position_conversion_factor_x = 1250 / self.x_track_length_in
        self.position_conversion_factor_y = 1371 / self.y_track_length_in
        self.left_y_axis_motor = Motor(Ports.PORT1, GearSetting.RATIO_18_1, False)
        self.right_y_axis_motor = Motor(Ports.PORT2, GearSetting.RATIO_18_1, True)
        self.left_x_axis_motor = Motor(Ports.PORT3, GearSetting.RATIO_18_1, True)
        self.right_x_axis_motor = Motor(Ports.PORT4, GearSetting.RATIO_18_1, True)

        self.left_y_axis_motor_controller = PIDController(0.7, 0, 0, 0.05, 0)
        self.right_y_axis_motor_controller = PIDController(0.7, 0, 0, 0.05, 0)
        self.x_axis_motor_controller = PIDController(0.6, 0, 0, 0.05, 0)

        self.pen = Servo(brain.three_wire_port.a)

    def setup(self):
        print("Setup")
        self.pen_up()
        self.calibrate()
        # self.draw_dxf("drawing.dxf")
        # self.draw_dxf("evans_drawing.dxf")

    def periodic(self):
        message = self.telemetry.get_message()
        if not message:
            return
        if "UP" in message:
            self.pen_up()
        elif "DOWN" in message:
            self.pen_down()
        elif "GOTO" in message:
            self.move_tool_to_position_linear([float(x) for x in message.split(":")[-1].split("|")], 0.5)

        self.brain.screen.print(message)
        self.brain.screen.next_row()

    def on_enable(self):
        print("Enable")

    def get_tool_position(self):
        return self.get_x_position(), self.get_y_position()

    def get_left_y_position(self):
        return self.left_y_axis_motor.position(DEGREES) / self.position_conversion_factor_y

    def get_right_y_position(self):
        return self.right_y_axis_motor.position(DEGREES) / self.position_conversion_factor_y

    def get_x_position(self):
        return MathUtil.average(self.left_x_axis_motor.position(DEGREES),
                                self.right_x_axis_motor.position(DEGREES)) / self.position_conversion_factor_x

    def get_y_position(self):
        return MathUtil.average(self.get_left_y_position(), self.get_right_y_position())

    def calibrate(self):

        self.left_x_axis_motor.spin(FORWARD, -1, VOLT)
        self.right_x_axis_motor.spin(FORWARD, -1, VOLT)
        time.sleep(1)
        while abs(self.left_x_axis_motor.velocity(PERCENT) + self.right_x_axis_motor.velocity(PERCENT)) > 10:
            time.sleep(0.1)
        self.left_x_axis_motor.set_position(0, DEGREES)
        self.right_x_axis_motor.set_position(0, DEGREES)

        self.left_x_axis_motor.set_velocity(0, PERCENT)
        self.right_x_axis_motor.set_velocity(0, PERCENT)
        self.left_x_axis_motor.spin(FORWARD)
        self.right_x_axis_motor.spin(FORWARD)
        print("Calibrated X")

        self.left_y_axis_motor.spin(FORWARD, -3, VOLT)
        self.right_y_axis_motor.spin(FORWARD, -3, VOLT)
        time.sleep(1)
        while abs(self.left_y_axis_motor.velocity(PERCENT) + self.right_y_axis_motor.velocity(PERCENT)) > 10:
            time.sleep(0.1)
        self.left_y_axis_motor.set_position(0, DEGREES)
        self.right_y_axis_motor.set_position(0, DEGREES)

        self.left_y_axis_motor.set_velocity(0, PERCENT)
        self.right_y_axis_motor.set_velocity(0, PERCENT)
        self.left_y_axis_motor.spin(FORWARD)
        self.right_y_axis_motor.spin(FORWARD)
        print("Calibrated Y")

        # self.y_axis_motor.spin(FORWARD, 5, VOLT)

    def move_tool_to_position_linear(self, position, speed):
        self.x_axis_motor_controller.setpoint = position[0]
        self.left_y_axis_motor_controller.setpoint = position[1]
        self.right_y_axis_motor_controller.setpoint = position[1]

        print("X current: " + str(self.get_x_position()))
        print("LY current: " + str(self.get_left_y_position()))
        print("RY current: " + str(self.get_right_y_position()))

        print("X current: " + str(self.get_x_position()))
        print("LY current: " + str(self.get_left_y_position()))
        print("RY current: " + str(self.get_right_y_position()))

        while not MathUtil.distance(self.get_tool_position(), position) < 0.05:
            print("TOOL: " + str(self.get_tool_position()))
            print("TARG: " + str(position))
            print("DIST: " + str(MathUtil.distance(self.get_tool_position(), position)))
            print("X SETPOINT: " + str(self.x_axis_motor_controller.setpoint))
            print("Y-L SETPOINT: " + str(self.left_y_axis_motor_controller.setpoint))
            print("Y-R SETPOINT: " + str(self.right_y_axis_motor_controller.setpoint))

            x_speed = self.x_axis_motor_controller.update(self.get_x_position()) * speed
            x_speed = MathUtil.clamp(x_speed, -0.3, 0.3)

            left_y_speed = self.left_y_axis_motor_controller.update(self.get_left_y_position()) * speed
            right_y_speed = self.right_y_axis_motor_controller.update(self.get_right_y_position()) * speed
            left_y_speed = MathUtil.clamp(left_y_speed, -0.3, 0.3)
            right_y_speed = MathUtil.clamp(right_y_speed, -0.3, 0.3)

            # x_speed += MathUtil.sign(x_speed) * 0.2
            # left_y_speed += MathUtil.sign(left_y_speed) * 1.4
            # right_y_speed += MathUtil.sign(right_y_speed) * 1.6

            # self.left_x_axis_motor.spin(FORWARD, x_speed, VOLT)
            # self.right_x_axis_motor.spin(FORWARD, x_speed, VOLT)
            self.left_x_axis_motor.set_velocity(x_speed * 100, PERCENT)
            self.right_x_axis_motor.set_velocity(x_speed * 100, PERCENT)

            # self.left_y_axis_motor.spin(FORWARD, left_y_speed, VOLT)
            # self.right_y_axis_motor.spin(FORWARD, right_y_speed, VOLT)
            self.left_y_axis_motor.set_velocity(left_y_speed * 100, PERCENT)
            self.right_y_axis_motor.set_velocity(right_y_speed * 100, PERCENT)

        self.left_x_axis_motor.set_velocity(0, PERCENT)
        self.right_x_axis_motor.set_velocity(0, PERCENT)
        self.left_y_axis_motor.set_velocity(0, PERCENT)
        self.right_y_axis_motor.set_velocity(0, PERCENT)
        print("Within tolerance")

    def follow_path(self, path, speed):
        for position in path:
            self.move_tool_to_position_linear(position, speed)

    def pen_down(self):
        self.pen.set_position(0, PERCENT)
        pass

    def pen_up(self):
        self.pen.set_position(100, PERCENT)
        pass

    def draw_square(self, side_length, bottom_left, movement_speed, drawing_speed):
        self.draw_rectangle(side_length, side_length, bottom_left, movement_speed, drawing_speed)

    def draw_rectangle(self, x_size, y_size, bottom_left, movement_speed, drawing_speed):
        start_point = self.get_tool_position()
        self.pen_up()
        self.move_tool_to_position_linear(bottom_left, movement_speed)
        self.pen_down()
        self.move_tool_to_position_linear((bottom_left[0] + x_size, bottom_left[0]), drawing_speed)
        self.move_tool_to_position_linear((bottom_left[0] + x_size, bottom_left[0] + y_size), drawing_speed)
        self.move_tool_to_position_linear((bottom_left[0], bottom_left[0] + y_size), drawing_speed)
        self.move_tool_to_position_linear(bottom_left, drawing_speed)
        self.pen_up()
        self.move_tool_to_position_linear(start_point, movement_speed)

    def draw_dxf(self, filename):
        # Load raw DXF content
        raw_dxf_content = open("deploy/" + str(filename), "r").read()

        # Create parser and parse the content
        dxf_parser = DXFParser(raw_dxf_content)
        dxf_parser.parse()

        lines = dxf_parser.extract_lines()
        combined_lines = dxf_parser.combine_lines(lines)

        self.pen_up()

        for line in combined_lines:
            line = [(MathUtil.clamp(point[0], 0, 5), MathUtil.clamp(point[1], 0, 5)) for point in line]
            self.move_tool_to_position_linear(line[0], 0.75)
            self.pen_down()
            time.sleep(1)
            self.follow_path(line, 0.5)
            self.pen_up()
            time.sleep(1)

        self.move_tool_to_position_linear((0, 0), 0.75)
