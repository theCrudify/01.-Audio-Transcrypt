import re
import unittest
from pathlib import Path

from app.config import WHISPER_LANGUAGES

from app.transcriber import parse_detected_language, pick_check_points, pick_gpu_device


def log(*devices):
    return "\n".join(
        f"whisper_backend_init_gpu: found GPU device {i}: Vulkan{i} (type: {t}, cnt: {i})"
        for i, t in enumerate(devices)
    )


class PickGpuDeviceTest(unittest.TestCase):
    def test_prefers_discrete_over_igpu(self):
        self.assertEqual(pick_gpu_device(log(2, 1)), 1)  # AMD laptop: 680M iGPU + RX 6500M
        self.assertEqual(pick_gpu_device(log(1, 2)), 0)  # NVIDIA Optimus listed first

    def test_igpu_only(self):
        self.assertEqual(pick_gpu_device(log(2)), 0)  # Intel Iris only

    def test_no_gpu_uses_cpu(self):
        self.assertIsNone(pick_gpu_device("whisper_backend_init_gpu: no GPU found"))


class ParseDetectedLanguageTest(unittest.TestCase):
    def test_parses_code_and_probability(self):
        log = "whisper_full_with_state: auto-detected language: id (p = 0.996314)\n"
        self.assertEqual(parse_detected_language(log), ("id", 0.996314))

    def test_missing_returns_none(self):
        self.assertIsNone(parse_detected_language("whisper_init: failed to load model"))


class PickCheckPointsTest(unittest.TestCase):
    def test_start_middle_end_of_speech(self):
        starts = [5, 100, 1795, 1810, 3500, 3590]
        self.assertEqual(pick_check_points(starts, 3600), [5, 1795, 3500])

    def test_short_file_single_point(self):
        self.assertEqual(pick_check_points([0, 4, 9], 11), [0])

    def test_no_speech(self):
        self.assertEqual(pick_check_points([], 120), [])



class LanguageListTest(unittest.TestCase):
    def test_ui_and_server_lists_match(self):
        html = (Path(__file__).resolve().parent.parent / "static" / "index.html").read_text(encoding="utf-8")
        ui = set(re.search(r"const WHISPER_LANGS = \('([^']+)'\)", html).group(1).split())
        self.assertEqual(ui, set(WHISPER_LANGUAGES))


if __name__ == "__main__":
    unittest.main()
