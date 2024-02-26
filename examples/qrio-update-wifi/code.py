# SPDX-FileCopyrightText: 2023 Jeff Epler for Adafruit Industries
# SPDX-FileCopyrightText: 2024 Tyeth Gundry for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""
This demo is designed for the Adafruit Memento ESP32-S3 Camera board.
It allows the shutter button to be checked in boot.py, and if pressed, it
will make the filesystem read-write, and then this code will allow updating
the wifi settings by scanning a QR code.  Existing valid TOML entries will
be saved, and the new ones will be written to the settings.toml file.
"""

import time
import toml
from toml._dotty import Dotty
import qrio
import storage
import os

from adafruit_pycamera import PyCamera

pycam = PyCamera()
pycam._mode_label.text = "QR SCAN"  # pylint: disable=protected-access
pycam._res_label.text = ""  # pylint: disable=protected-access
pycam.effect = 0
pycam.camera.hmirror = False
pycam.display.refresh()
qrdecoder = qrio.QRDecoder(pycam.camera.width, pycam.camera.height)

old_payload = None
while True:
    new_frame = pycam.continuous_capture()
    if new_frame is None:
        continue
    pycam.blit(new_frame)
    for row in qrdecoder.decode(new_frame, qrio.PixelPolicy.RGB565_SWAPPED):
        print(row)
        payload = row.payload
        try:
            payload = payload.decode("utf-8")
        except UnicodeError:
            payload = str(payload)
        if payload != old_payload:
            pycam.tone(200, 0.1)

            if payload.startswith("WIFI:"):
                pycam.display_message("WIFI", color=0xFFFFFF, scale=2)
                pycam.tone(140, 0.5)

                old_ssid=os.getenv("CIRCUITPY_WIFI_SSID", None)
                old_password=os.getenv("CIRCUITPY_WIFI_PASSWORD", None)

                start_of_ssid = payload.find("S:")+2
                new_ssid = str(payload[
                    start_of_ssid
                    :
                    start_of_ssid + payload[start_of_ssid:].find(";")
                    ])

                start_of_pass = payload.find("P:")+2
                new_pass = str(payload[start_of_pass:start_of_pass + payload[start_of_pass:].find(";")])
                print("Supplied SSID:", new_ssid, "PASS:", new_pass)

                if old_ssid != new_ssid or old_password != new_pass:
                    # os.setenv("CIRCUITPY_WIFI_SSID", new_ssid)
                    #get file object:
                    print("Updating settings.toml")
                    with open("/settings.toml", "r") as f:
                        try:
                            old_toml = dict()
                            lines = f.readlines()
                            for i,w in enumerate(lines):
                                try:
                                    print(f"TOML Line #{i}: {str(w).strip()}")
                                    new_toml_section = toml.loads(str(w).strip())
                                    old_toml.update(new_toml_section._data)
                                    # print("Added:",new_toml_section)
                                except (toml.TOMLError, KeyError) as e:
                                    print("TOML ERROR - Skipping key:", e)
                                    pass
                            print(old_toml)
                        except:
                            raise
                            old_toml = {}
                    old_toml["CIRCUITPY_WIFI_SSID"] = new_ssid
                    old_toml["CIRCUITPY_WIFI_PASSWORD"] = new_pass
                    pycam.display_message("WIFI CHANGING...", color=0xFFFFFF, scale=2)
                    pycam.tone(320, 0.25)
                    # check if circuitpython fs is writeable
                    if storage.getmount("/").readonly:
                        pycam.display_message("FS READONLY!\n Hold Shutter \nwhen bootlog shown", color=0xFFFFFF, scale=2)
                        print("FS READONLY! Hold select when bootlog shown")
                        pycam.tone(560, 0.25)
                        time.sleep(2.5)
                    else:
                        with open("/settings.toml", "w") as f:
                            f.write(toml.dumps(old_toml))
                        pycam.display_message("WIFI CHANGED!", color=0xFFFFFF, scale=2)
                        print("WIFI CHANGED! Settings.toml updated, Reboot to take affect")
                        pycam.tone(440, 0.25)
                    time.sleep(1)
                    timeleft=65
                    msg = "Would you like to \njoin network now? \nPress Shutter if yes\n    %s"
                    pycam.keys_debounce()
                    while not pycam.shutter.pressed and timeleft > 0:
                        timeleft -= 1
                        # NB: note that this is really bad! it should only update when needed,
                        # or it will take longer than expected updating with the same image
                        pycam.display_message(msg % (timeleft//20), color=0xFFFFFF, scale=2)
                        time.sleep(0.05)
                        pycam.keys_debounce()
                    
                    if pycam.shutter.pressed:
                        pycam.display_message("Joining Network...", color=0xFFFFFF, scale=2)
                        import wifi
                        wifi.radio.enabled = False
                        time.sleep(0.1)
                        wifi.radio.enabled = True
                        wifi.radio.connect(new_ssid, new_pass)
                        time.sleep(0.75)
                        pycam.display_message("", color=0xFFFFFF, scale=2)
                    

            print(payload)
            pycam.display_message(payload, color=0xFFFFFF, scale=1)
            time.sleep(1)
            old_payload = payload

