def main():
    while True:
        from vex import Brain, Thread, wait, MSEC
        brain = Brain()
        if not brain.sdcard.is_inserted():
            brain.screen.print("Please insert the SD card")
            print("Please insert the SD card")
            while not brain.sdcard.is_inserted():
                wait(50, MSEC)
            wait(1000, MSEC)  # Make sure that the SD card is well-situated
            brain.screen.clear_screen()
            brain.screen.set_cursor(1, 1)
        from Robot import Robot
        from VEXLib.Util import time as time
        import sys

        robot = Robot(brain)

        robot_thread = Thread(robot.start)

        while not robot.restart_requested:
            time.sleep(0.05)
        print("Restarting robot")
        robot_thread.stop()
        robot.on_disable()
        robot.on_driver_control_disable()
        robot.on_autonomous_disable()
        del robot  # Delete the robot instance

        for module_name in sys.modules.keys():
            print("Wiping cached module: " + str(sys.modules[module_name]))
            del sys.modules[module_name]
        if len(sys.modules) == 0:
            print("Successfully cleared all cached modules")
        else:
            raise RuntimeError("Failed to clear all cached modules, remaining: " + str(sys.modules))
