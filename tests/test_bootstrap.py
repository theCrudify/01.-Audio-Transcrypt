import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from app import bootstrap


class DownloadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.source = self.tmp / "source.bin"
        self.source.write_bytes(b"model-bytes" * 1000)
        self.sha = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def test_good_checksum_creates_file(self):
        target = self.tmp / "out" / "model.bin"
        bootstrap.download(self.source.as_uri(), target, self.sha)
        self.assertEqual(target.read_bytes(), self.source.read_bytes())
        self.assertFalse(target.with_name("model.bin.part").exists())

    def test_bad_checksum_leaves_nothing(self):
        target = self.tmp / "model.bin"
        with self.assertRaises(bootstrap.SetupError):
            bootstrap.download(self.source.as_uri(), target, "0" * 64)
        self.assertFalse(target.exists())
        self.assertFalse(target.with_name("model.bin.part").exists())

    def test_windows_bundle_is_extracted(self):
        bundle = self.tmp / "bundle.zip"
        with zipfile.ZipFile(bundle, "w") as zf:
            zf.writestr("whisper-cli.exe", b"exe")
            zf.writestr("ggml-vulkan.dll", b"dll")
        sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
        cli_dir = self.tmp / "build-vulkan" / "bin" / "Release"
        with mock.patch.multiple(
            bootstrap, BASE_DIR=self.tmp, WINDOWS_CLI_DIR=cli_dir,
            WINDOWS_BINARY_URL=bundle.as_uri(), WINDOWS_BINARY_SHA256=sha, ensure_vc_runtime=mock.DEFAULT,
        ):
            bootstrap.ensure_windows_cli()
        self.assertTrue((cli_dir / "whisper-cli.exe").is_file())
        self.assertTrue((cli_dir / "ggml-vulkan.dll").is_file())
        self.assertFalse((self.tmp / "build-vulkan" / "whisper-vulkan-windows-x64.zip").exists())

    def test_windows_falls_back_to_official_cpu_build_then_upgrades(self):
        def make_zip(path, files):
            with zipfile.ZipFile(path, "w") as zf:
                for name, data in files.items():
                    zf.writestr(name, data)
            return hashlib.sha256(path.read_bytes()).hexdigest()

        cpu = self.tmp / "cpu.zip"
        cpu_sha = make_zip(cpu, {"Release/whisper-cli.exe": b"cpu", "Release/ggml-cpu-x64.dll": b"d", "Release/bench.exe": b"x"})
        cli_dir = self.tmp / "build-vulkan" / "bin" / "Release"
        patches = dict(
            BASE_DIR=self.tmp, WINDOWS_CLI_DIR=cli_dir, ensure_vc_runtime=mock.DEFAULT,
            WINDOWS_BINARY_URL=(self.tmp / "missing.zip").as_uri(), WINDOWS_BINARY_SHA256="0" * 64,
            OFFICIAL_CPU_URL=cpu.as_uri(), OFFICIAL_CPU_SHA256=cpu_sha,
        )
        with mock.patch.multiple(bootstrap, **patches):
            bootstrap.ensure_windows_cli()
        self.assertEqual((cli_dir / "whisper-cli.exe").read_bytes(), b"cpu")
        self.assertTrue((cli_dir / "CPU_ONLY.txt").is_file())
        self.assertFalse((cli_dir / "bench.exe").exists())

        vulkan = self.tmp / "vulkan.zip"
        patches.update(WINDOWS_BINARY_URL=vulkan.as_uri(), WINDOWS_BINARY_SHA256=make_zip(vulkan, {"whisper-cli.exe": b"gpu"}))
        with mock.patch.multiple(bootstrap, **patches):
            bootstrap.ensure_windows_cli()
        self.assertEqual((cli_dir / "whisper-cli.exe").read_bytes(), b"gpu")
        self.assertFalse((cli_dir / "CPU_ONLY.txt").exists())
        self.assertFalse((cli_dir / "ggml-cpu-x64.dll").exists())

    def test_vc_runtime_found_in_system_or_app_dir(self):
        system, app = self.tmp / "System32", self.tmp / "app"
        system.mkdir(); app.mkdir()
        self.assertEqual(bootstrap.missing_vc_runtime(system, app), list(bootstrap.VC_RUNTIME_DLLS))
        for name in bootstrap.VC_RUNTIME_DLLS[:3]:
            (system / name).write_bytes(b"dll")
        (app / "vcomp140.dll").write_bytes(b"dll")
        self.assertEqual(bootstrap.missing_vc_runtime(system, app), [])


if __name__ == "__main__":
    unittest.main()
