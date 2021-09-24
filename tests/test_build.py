from unittest.mock import patch

import runez

from portable_python.versions import PPG

from .conftest import dummy_tarball


def test_build_rc(cli):
    f = PPG.get_folders(version="3.10.0rc2")
    install_dir = f.resolved_destdir()
    cli.run("-n", "-tmacos-arm64", "build", f.version, "-mnone")
    assert cli.succeeded
    assert f"Would tar {install_dir} -> dist/cpython-{f.version}-macos-arm64.tar.gz" in cli.logged


def test_finalization(cli, monkeypatch):
    f = PPG.get_folders(version="3.9.7")
    dummy_tarball(f, f"Python-{f.version}.tar.xz")
    dummy_tarball(f, "bzip2-1.0.8.tar.gz")
    bin = f.resolved_destdir("bin")
    runez.touch(f.components / "cpython/README", logger=None)

    # Create some files to be groomed by CPython
    runez.touch(bin.parent / "lib/idle_test/foo", logger=None)
    runez.touch(bin.parent / "lib/__phello__.foo.py", logger=None)
    runez.touch(bin / "foo-python", logger=None)
    runez.touch(bin / f"pip{f.mm}", logger=None)
    runez.symlink(bin / "foo-python", bin / "python3", logger=None)  # Simulate a funky symlink, to test edge cases
    runez.write(bin / "some-exe", "#!.../bin/python3\nhello", logger=None)
    runez.write(bin / "some-exe2", "#!/bin/sh\nhello", logger=None)
    runez.write(bin / "some-exe3", b"\xe4", logger=None)  # Non-unicode char to trigger edge case
    pd = bin.parent / "lib/python3.9/config-3.9/pythond"
    runez.write(pd, "#!.../bin/python3\nhello", logger=None)
    runez.make_executable(bin / "some-exe", logger=None)
    runez.make_executable(bin / "some-exe2", logger=None)
    runez.make_executable(bin / "some-exe3", logger=None)
    runez.make_executable(pd, logger=None)
    monkeypatch.setenv("PP_X_DEBUG", "direct-finalize")
    with patch("runez.run", return_value=runez.program.RunResult(code=0)):
        cli.run("-tlinux-x86_64", "-c", cli.tests_path("sample-config1.yml"), "build", f.version, "-mbzip2")
        assert cli.failed
        assert "selected: bzip2" in cli.logged
        assert "INFO Cleaned 2 build artifacts (0 B): __phello__.foo.py idle_test" in cli.logged
        assert f"Symlink {bin}/foo-python <- {bin}/python" in cli.logged
        assert f"Symlink {bin}/pip{f.mm} <- {bin}/pip" in cli.logged
        assert f"Auto-corrected shebang for {bin}/some-exe" in cli.logged
        assert "Build failed" in cli.logged

    assert list(runez.readlines(bin / "some-exe")) == ["#!/bin/sh", '"exec" "$(dirname $0)/foo-python" "$0" "$@"', "hello"]
    assert list(runez.readlines(bin / "some-exe2")) == ["#!/bin/sh", "hello"]
    assert runez.basename(bin / "python", follow=True) == "foo-python"

    with patch("runez.run", return_value=runez.program.RunResult(code=0)):
        cli.run("-tmacos-arm64", "-c", cli.tests_path("sample-config1.yml"), "build", f.version, "-mbzip2")
        assert cli.failed
        assert f"Deleted {bin}/pip{f.mm}" in cli.logged
        assert f"Cleaned 2 build artifacts (0 B): pip pip{f.mm}" in cli.logged
        assert cli
