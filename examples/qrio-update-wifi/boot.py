# SPDX-FileCopyrightText: 2023 Jeff Epler for Adafruit Industries
# SPDX-FileCopyrightText: 2024 Tyeth Gundry for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""Automatically create the /sd mount point at boot time"""

import os
import storage
import time
import digitalio
import board
from digitalio import Pull
storage.remount("/", readonly=False)

try:
    os.mkdir("/sd")
except OSError:
    pass  # It's probably 'file exists', OK to ignore

shutter_button = digitalio.DigitalInOut(board.BUTTON)
shutter_button.switch_to_input(Pull.UP)
print("")
print("Waiting 2.5s before checking if Shutter button held")
time.sleep(2.5)
if not shutter_button.value:
    print("")
    print("")
    print("Button held, MEMENTO = Flash WRITEABLE")
    print("")
    print("")
else:
    print("")
    print("")
    print("Button not held, USB = WRITEABLE")
    print("")
    print("")
    storage.remount("/", readonly=True)

