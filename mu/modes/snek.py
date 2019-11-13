"""
A mode for working with Snek boards. https://keithp.com/snek

Copyright © 2019 Keith Packard

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import logging
from .base import MicroPythonMode
from .api import SNEK_APIS
from mu.interface.panes import CHARTS
from PyQt5.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


class SnekMode(MicroPythonMode):
    """
    Represents the functionality required by the Snek mode.
    """

    name = _("Snek")
    description = _("Write code for boards running Snek.")
    icon = "snek"
    save_timeout = 0  #: No auto-save on CP boards. Will restart.
    connected = True  #: is the board connected.
    force_interrupt = True  #: keyboard interrupt on serial connection.
    valid_boards = [
        (0xFFFE, None),  # Any misc Altusmetrum USB board.
        (0x239A, 0x8022),  # Feather M0 Express
        (0x239A, 0x8011),  # ItsyBitsy M0
        (0x239A, 0x8013),  # Metro M0 Express
        (0x239A, 0x8018),  # Circuit Playground Express
        (0x239A, 0x804D),  # Snekboard
        (0x1366, 0x1051),  # Hifive1 revb
        (0x2341, 0x8057),  # Arduino SA Nano 33 IoT
        (0x0403, 0x6001),  # Duemilanove with FT232
        (0x03EB, 0x204B),  # Arduino Mega with LUFA
    ]
    # Run these boards at 38400 baud
    slow_boards = [(0x03EB, 0x204B)]  # Arduino Mega with LUFA
    # Modules built into Snek which mustn't be used as file names
    # for source code.
    module_names = {"time", "random", "math"}
    builtins = (
        "A0",
        "A1",
        "A10",
        "A11",
        "A12",
        "A13",
        "A14",
        "A15",
        "A2",
        "A3",
        "A4",
        "A5",
        "A6",
        "A7",
        "A8",
        "A9",
        "BUTTONA",
        "BUTTONB",
        "CAP1",
        "CAP2",
        "CAP3",
        "CAP4",
        "D0",
        "D1",
        "D10",
        "D11",
        "D12",
        "D13",
        "D14",
        "D15",
        "D16",
        "D17",
        "D18",
        "D19",
        "D2",
        "D20",
        "D21",
        "D22",
        "D23",
        "D24",
        "D25",
        "D26",
        "D27",
        "D28",
        "D29",
        "D3",
        "D30",
        "D31",
        "D32",
        "D33",
        "D34",
        "D35",
        "D36",
        "D37",
        "D38",
        "D39",
        "D4",
        "D40",
        "D41",
        "D42",
        "D43",
        "D44",
        "D45",
        "D46",
        "D47",
        "D48",
        "D49",
        "D5",
        "D50",
        "D51",
        "D52",
        "D53",
        "D6",
        "D7",
        "D8",
        "D9",
        "DRIVE1",
        "DRIVE2",
        "DRIVE3",
        "DRIVE4",
        "FLASHCS",
        "FLASHMISO",
        "FLASHMOSI",
        "FLASHSCK",
        "I2SCK",
        "I2SDO",
        "LED",
        "LIGHT",
        "LISIRQ",
        "LISSCL",
        "LISSDA",
        "M1",
        "M2",
        "M3",
        "M4",
        "MISO",
        "MOSI",
        "MOTOR1",
        "MOTOR2",
        "NEOPIXEL",
        "NEOPIXEL1",
        "REMOTEIN",
        "REMOTEOUT",
        "RX",
        "SCK",
        "SCL",
        "SDA",
        "SERVO1",
        "SERVO2",
        "SERVO3",
        "SERVO4",
        "SIGNAL1",
        "SIGNAL2",
        "SIGNAL3",
        "SIGNAL4",
        "SIGNAL5",
        "SIGNAL6",
        "SIGNAL7",
        "SIGNAL8",
        "SWITCH",
        "TEMP",
        "TX",
        "abs_tol",
        "curses",
        "eeprom",
        "exit",
        "math",
        "neopixel",
        "off",
        "on",
        "onfor",
        "pulldown",
        "pullnone",
        "pullup",
        "random",
        "read",
        "rel_tol",
        "reset",
        "round",
        "setleft",
        "setpower",
        "setright",
        "stdscr",
        "stopall",
        "sys",
        "talkto",
        "temperature",
        "time",
    )

    def stop(self):
        self.view.close_serial_link()

    def actions(self):
        """
        Return an ordered list of actions provided by this module. An action
        is a name (also used to identify the icon) , description, and handler.
        """
        buttons = [
            {
                "name": "serial",
                "display_name": _("Serial"),
                "description": _("Open a serial connection to your device."),
                "handler": self.toggle_repl,
                "shortcut": "CTRL+Shift+U",
            },
            {
                "name": "flash",
                "display_name": _("Put"),
                "description": _("Put the current program to the device."),
                "handler": self.put,
                "shortcut": "CTRL+Shift+P",
            },
            {
                "name": "getflash",
                "display_name": _("Get"),
                "description": _("Get the current program from the device."),
                "handler": self.get,
                "shortcut": "CTRL+Shift+G",
            },
        ]
        if CHARTS:
            buttons.append(
                {
                    "name": "plotter",
                    "display_name": _("Plotter"),
                    "description": _("Plot incoming REPL data."),
                    "handler": self.toggle_plotter,
                    "shortcut": "CTRL+Shift+P",
                }
            )
        return buttons

    def put(self):
        """
        Put the current program into the device memory.
        """
        logger.info("Downloading code to target device.")
        # Grab the Python script.
        tab = self.view.current_tab
        if tab is None:
            # There is no active text editor.
            message = _("Cannot run anything without any active editor tabs.")
            information = _(
                "Running transfers the content of the current tab"
                " onto the device. It seems like you don't have "
                " any tabs open."
            )
            self.view.show_message(message, information)
            return
        python_script = tab.text()
        if python_script[-1] != "\n":
            python_script += "\n"
        if not self.repl:
            self.toggle_repl(None)
        command = ("eeprom.write()\n" + python_script + "\x04" + "reset()\n",)
        if self.repl:
            self.view.repl_pane.send_commands(command)

    def get_tab(self):
        for tab in self.view.widgets:
            if not tab.path:
                return tab
        return None

    def recv_text(self, text):
        target_tab = self.get_tab()
        if target_tab:
            target_tab.setText(text)
            target_tab.setModified(False)
        else:
            view = self.view
            editor = self.editor
            view.add_tab(None, text, editor.modes[editor.mode].api(), "\n")

    def get(self):
        """
        Get the current program from device memory.
        """
        target_tab = self.get_tab()
        if target_tab and target_tab.isModified():
            msg = "There is un-saved work, 'get' will cause you " "to lose it."
            window = target_tab.nativeParentWidget()
            if window.show_confirmation(msg) == QMessageBox.Cancel:
                return

        command = ("eeprom.show(1)\n",)
        if not self.repl:
            self.toggle_repl(None)
        if self.repl:
            self.view.repl_pane.text_recv = self
            self.view.repl_pane.send_commands(command)

    def api(self):
        """
        Return a list of API specifications to be used by auto-suggest and call
        tips.
        """
        return SNEK_APIS

    def add_repl(self):
        """
        Detect a connected Snek based device and, if found, connect to
        the REPL and display it to the user.
        """
        device_port, serial_number = self.find_device()
        if device_port:
            try:
                rate = 38400
                if (self.vid, self.pid) not in self.slow_boards:
                    rate = 115200
                self.view.add_snek_repl(
                    device_port, self.name, self.force_interrupt, rate=rate
                )
                logger.info("Started REPL on port: {}".format(device_port))
            except IOError as ex:
                logger.error(ex)
                self.view.remove_repl()
                info = _(
                    "Click on the device's reset button, wait a few"
                    " seconds and then try again."
                )
                self.view.show_message(str(ex), info)
            except Exception as ex:
                logger.error(ex)
        else:
            message = _("Could not find an attached device.")
            information = _(
                "Please make sure the device is plugged into this"
                " computer.\n\nIt must have a version of"
                " Snek flashed onto it"
                " before the REPL will work.\n\nFinally, press the"
                " device's reset button and wait a few seconds"
                " before trying again."
            )
            self.view.show_message(message, information)
