"""
This file goes on the vex brain over a USB cable; the rest of the code can be pushed to an SD card using deploy.py
"""

from vex import *

brain = Brain()

if not brain.sdcard.is_inserted():
    brain.screen.print("Please insert the SD card")
    while not brain.sdcard.is_inserted():
        wait(50, MSEC)
    wait(1000, MSEC)  # Make sure that the SD card is well-situated
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)

del brain  # Clean up resources used by the brain instance

import main
main.main()
