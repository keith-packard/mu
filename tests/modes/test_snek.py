# -*- coding: utf-8 -*-
"""
Tests for the Snek mode.
"""
from mu.modes.snek import SnekMode
from mu.modes.api import SNEK_APIS
from PyQt5.QtWidgets import QMessageBox
from unittest import mock


def test_snek_mode():
    """
    Sanity check for setting up the mode.
    """
    editor = mock.MagicMock()
    view = mock.MagicMock()
    am = SnekMode(editor, view)
    assert am.name == "Snek"
    assert am.description is not None
    assert am.icon == "snek"
    assert am.editor == editor
    assert am.view == view

    actions = am.actions()
    assert len(actions) == 4
    assert actions[0]["name"] == "serial"
    assert actions[0]["handler"] == am.toggle_repl
    assert actions[1]["name"] == "flash"
    assert actions[1]["handler"] == am.put
    assert actions[2]["name"] == "getflash"
    assert actions[2]["handler"] == am.get
    assert actions[3]["name"] == "plotter"
    assert actions[3]["handler"] == am.toggle_plotter
    assert "code" not in am.module_names


def test_snek_mode_no_charts():
    """
    If QCharts is not available, ensure the plotter feature is not available.
    """
    editor = mock.MagicMock()
    view = mock.MagicMock()
    am = SnekMode(editor, view)
    with mock.patch("mu.modes.snek.CHARTS", False):
        actions = am.actions()
        assert len(actions) == 3
        assert actions[0]["name"] == "serial"
        assert actions[0]["handler"] == am.toggle_repl
        assert actions[1]["name"] == "flash"
        assert actions[1]["handler"] == am.put
        assert actions[2]["name"] == "getflash"
        assert actions[2]["handler"] == am.get


def test_put():
    """
    Put current editor contents to eeprom
    """

    class TestSnekMode(SnekMode):
        def toggle_repl(self, event):
            self.repl = True

    editor = mock.MagicMock()
    view = mock.MagicMock()
    mock_tab = mock.MagicMock()
    mock_tab.text.return_value = "# Write your code here :-)"
    view.current_tab = mock_tab
    view.repl_pane = mock.MagicMock()
    view.repl_pane.send_commands = mock.MagicMock()
    mm = TestSnekMode(editor, view)
    mm.repl = None
    mm.put()
    assert view.repl_pane.send_commands.call_count == 1


def test_put_none():
    """
    Put current editor contents to eeprom
    """
    editor = mock.MagicMock()
    view = mock.MagicMock()
    view.current_tab = None
    view.repl_pane = mock.MagicMock()
    view.repl_pane.send_commands = mock.MagicMock()
    view.show_message = mock.MagicMock()
    mm = SnekMode(editor, view)
    mm.put()
    assert view.show_message.call_count == 1


mm = None


def set_repl(*args, **kwargs):
    mm.repl = True


def test_get_new():
    """
    Get current editor contents to eeprom
    """
    global mm
    editor = mock.MagicMock()
    view = mock.MagicMock()
    view.repl_pane = mock.MagicMock()
    view.repl_pane.send_commands = mock.MagicMock()
    view.widgets = ()
    view.add_tab = mock.MagicMock()
    mm = SnekMode(editor, view)
    mm.repl = False
    mm.toggle_repl = mock.MagicMock()
    mm.toggle_repl.side_effect = set_repl
    mm.get()
    assert mm.toggle_repl.call_count == 1
    assert view.repl_pane.send_commands.call_count == 1
    mm.recv_text("hello")
    assert view.add_tab.call_count == 1


def test_get_existing():
    """
    Get current editor contents to eeprom
    """
    editor = mock.MagicMock()
    view = mock.MagicMock()
    tab = mock.MagicMock()
    tab.path = None
    tab.setText = mock.MagicMock()
    tab.setModified(False)
    view.repl_pane = mock.MagicMock()
    view.repl_pane.send_commands = mock.MagicMock()
    view.widgets = (tab,)
    mm = SnekMode(editor, view)
    mm.repl = True
    mm.get()
    assert view.repl_pane.send_commands.call_count == 1
    mm.recv_text("hello")
    assert tab.setText.call_count == 1


def test_get_existing_modified():
    """
    Get current editor contents into a modified buffer from eeprom
    """
    editor = mock.MagicMock()
    view = mock.MagicMock()
    tab = mock.MagicMock()
    tab.path = None
    tab.setText = mock.MagicMock()
    tab.isModified.return_value = True

    mock_window = mock.MagicMock()
    mock_window.show_confirmation = mock.MagicMock(
        return_value=QMessageBox.Cancel
    )
    tab.nativeParentWidget = mock.MagicMock(return_value=mock_window)
    view.repl_pane = mock.MagicMock()
    view.repl_pane.send_commands = mock.MagicMock()
    view.widgets = (tab,)
    mm = SnekMode(editor, view)
    mm.repl = True
    mm.get()
    assert mock_window.show_confirmation.call_count == 1
    assert view.repl_pane.send_commands.call_count == 0


def test_api():
    """
    Ensure the correct API definitions are returned.
    """
    editor = mock.MagicMock()
    view = mock.MagicMock()
    am = SnekMode(editor, view)
    assert am.api() == SNEK_APIS


def test_snek_mode_add_repl_no_port():
    """
    If it's not possible to find a connected micro:bit then ensure a helpful
    message is enacted.
    """
    editor = mock.MagicMock()
    view = mock.MagicMock()
    view.show_message = mock.MagicMock()
    mm = SnekMode(editor, view)
    mm.find_device = mock.MagicMock(return_value=(None, None))
    mm.add_repl()
    assert view.show_message.call_count == 1
    message = "Could not find an attached device."
    assert view.show_message.call_args[0][0] == message


def test_snek_mode_add_repl_ioerror():
    """
    Sometimes when attempting to connect to the device there is an IOError
    because it's still booting up or connecting to the host computer. In this
    case, ensure a useful message is displayed.
    """
    editor = mock.MagicMock()
    view = mock.MagicMock()
    view.show_message = mock.MagicMock()
    ex = IOError("BOOM")
    view.add_snek_repl = mock.MagicMock(side_effect=ex)
    mm = SnekMode(editor, view)
    mm.find_device = mock.MagicMock(return_value=("COM0", "12345"))
    mm.add_repl()
    assert view.show_message.call_count == 1
    assert view.show_message.call_args[0][0] == str(ex)


def test_snek_mode_add_repl_exception():
    """
    Ensure that any non-IOError based exceptions are logged.
    """
    editor = mock.MagicMock()
    view = mock.MagicMock()
    ex = Exception("BOOM")
    view.add_snek_repl = mock.MagicMock(side_effect=ex)
    mm = SnekMode(editor, view)
    mm.find_device = mock.MagicMock(return_value=("COM0", "12345"))
    with mock.patch("mu.modes.snek.logger", return_value=None) as logger:
        mm.add_repl()
        logger.error.assert_called_once_with(ex)


def test_snek_mode_add_repl():
    """
    Nothing goes wrong so check the _view.add_snek_repl gets the
    expected argument.
    """
    editor = mock.MagicMock()
    view = mock.MagicMock()
    view.show_message = mock.MagicMock()
    view.add_snek_repl = mock.MagicMock()
    mm = SnekMode(editor, view)
    mm.find_device = mock.MagicMock(return_value=("COM0", "12345"))
    with mock.patch("os.name", "nt"):
        mm.add_repl()
    assert view.show_message.call_count == 0
    assert view.add_snek_repl.call_args[0][0] == "COM0"


def test_snek_mode_add_repl_no_force_interrupt():
    """
    Nothing goes wrong so check the _view.add_snek_repl gets the
    expected arguments (including the flag so no keyboard interrupt is called).
    """
    editor = mock.MagicMock()
    view = mock.MagicMock()
    view.show_message = mock.MagicMock()
    view.add_snek_repl = mock.MagicMock()
    mm = SnekMode(editor, view)
    mm.force_interrupt = False
    mm.find_device = mock.MagicMock(return_value=("COM0", "12345"))
    with mock.patch("os.name", "nt"):
        mm.add_repl()
    assert view.show_message.call_count == 0
    assert view.add_snek_repl.call_args[0][0] == "COM0"
    assert view.add_snek_repl.call_args[0][2] is False


def test_snek_stop():
    """
    Ensure that this method, called when Mu is quitting, shuts down
    the serial port.
    """
    editor = mock.MagicMock()
    view = mock.MagicMock()
    mm = SnekMode(editor, view)
    view.close_serial_link = mock.MagicMock()
    mm.stop()
    view.close_serial_link.assert_called_once_with()
