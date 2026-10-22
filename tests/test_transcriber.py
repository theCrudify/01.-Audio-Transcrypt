import unittest

from app.transcriber import pick_gpu_device


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


if __name__ == "__main__":
    unittest.main()
