import importlib
import unittest
from unittest.mock import MagicMock, patch


class TestPluginSystem(unittest.TestCase):
    @patch("bridge.eeg.config.init_functions", [MagicMock()])
    @patch("bridge.eeg.config.close_functions", [MagicMock()])
    def test_init_and_close_call_registered_functions(self) -> None:
        """
        Verify that eeg.init() and eeg.close() call the functions
        registered by the plugin system.
        """
        from bridge.eeg.config import close, close_functions, init, init_functions

        init_func_mock = init_functions[0]
        close_func_mock = close_functions[0]

        init()
        init_func_mock.assert_called_once()
        close_func_mock.assert_not_called()

        init()
        self.assertEqual(init_func_mock.call_count, 2, "Expected init function to be called a second time.")

        close()
        close_func_mock.assert_called_once()
        self.assertEqual(init_func_mock.call_count, 2)

    def test_logs_warning_when_no_plugins_are_loaded(self) -> None:
        """
        Verify that a WARNING is logged if the devices module is loaded and no
        device classes were successfully registered.
        """
        import bridge.eeg.config

        with patch.dict("sys.modules", {"brainaccess": None}):
            with self.assertLogs("bridge.eeg.config", level="WARNING") as cm:
                importlib.reload(bridge.eeg.config)

        self.assertTrue(
            any("No EEG device classes registered" in message for message in cm.output),
            "Expected warning log message not found.",
        )
