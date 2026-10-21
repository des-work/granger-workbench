from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import device_health as dh


class DeviceHealthTests(unittest.TestCase):
    def test_cpu_parses_loadavg_and_sensors(self):
        sensors_out = "coretemp-isa-0000\nPackage id 0:  +71.0°C  (high = +110.0°C)\n"
        with patch.object(dh.Path, "read_text", return_value="0.36 0.38 0.61 1/3284 67138\n"), \
             patch.object(dh, "_run", side_effect=["22\n", sensors_out]):
            reading = dh.cpu()
        self.assertEqual(reading["load_1m"], 0.36)
        self.assertEqual(reading["cores"], 22)
        self.assertEqual(reading["package_temp_c"], 71.0)

    def test_gpu_parses_nvidia_smi_csv(self):
        line = "NVIDIA GeForce RTX 4080 Laptop GPU, 49, 7348, 12282, 23, 6.64\n"
        with patch.object(dh, "_run", return_value=line):
            reading = dh.gpu()
        self.assertEqual(reading["name"], "NVIDIA GeForce RTX 4080 Laptop GPU")
        self.assertEqual(reading["temperature_c"], 49.0)
        self.assertEqual(reading["utilization_percent"], 23.0)

    def test_gpu_unavailable_does_not_raise(self):
        with patch.object(dh, "_run", return_value=None):
            self.assertEqual(dh.gpu(), {"error": "unavailable"})

    def test_battery_distinguishes_charge_from_health(self):
        info = "state:               fully-charged\npercentage:          91%\ncapacity:            85.3968%\n"
        with patch.object(dh, "_run", side_effect=["BAT1\n", info]):
            reading = dh.battery()
        self.assertEqual(reading["percentage"], 91.0)
        self.assertEqual(reading["capacity_health_percent"], 85.3968)

    def test_battery_absent_reports_present_false(self):
        with patch.object(dh, "_run", return_value=""):
            self.assertEqual(dh.battery(), {"present": False})

    def test_rpc_tools_call_returns_a_full_snapshot(self):
        with patch.object(dh, "snapshot", return_value={"cpu": {}, "gpu": {}}):
            result = dh.rpc({"method": "tools/call", "params": {"name": "device_health", "arguments": {}}})
        self.assertNotIn("isError", result)
        self.assertIn("cpu", result["content"][0]["text"])

    def test_rpc_rejects_unknown_tool(self):
        result = dh.rpc({"method": "tools/call", "params": {"name": "nope", "arguments": {}}})
        self.assertTrue(result["isError"])


if __name__ == "__main__":
    unittest.main()
