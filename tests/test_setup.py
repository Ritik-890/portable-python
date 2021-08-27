import runez

from portable_python import BuildSetup, ModuleBuilder, PythonInspector
from portable_python.versions import PythonVersions


def test_edge_cases():
    latest = PythonVersions.cpython.latest
    setup = BuildSetup(latest, target="linux-x86_64")
    assert setup.target_system.is_linux
    assert str(setup).endswith(f"build/cpython-{latest}")
    assert str(setup.python_builder) == f"cpython:{latest}"
    assert str(PythonVersions.cpython).startswith("cpython ")

    mb = ModuleBuilder()
    assert not mb.url
    assert not mb.version

    inspector = PythonInspector("0.1.2")
    r0 = inspector.reports[0]
    assert str(r0) == "0.1.2 [not available]"
    assert r0.color("*absent*")
    assert r0.color("built-in")
    assert r0.color("foo")

    inspector.reports[0].python.problem = None
    inspector.reports[0].report = runez.program.RunResult(code=0, output="foo")
    assert inspector.report() == "0.1.2 [cpython:0.1.2]:\nfoo"

    inspector.reports[0].report = runez.program.RunResult(code=1, output="foo")
    assert inspector.report() == "0.1.2 [cpython:0.1.2]:\n-- exit_code: 1\n-- output: foo"


def test_inspect_module(logged):
    # Exercise _inspect code
    import portable_python._inspect

    portable_python._inspect.main()
    assert '"readline": "' in logged.pop()

    portable_python._inspect.main(["sysconfig"])
    assert "VERSION:" in logged.pop()

    all_modules = portable_python._inspect.get_modules("all")
    assert "_tracemalloc" in all_modules

    # Verify convenience parsing works
    base = portable_python._inspect.get_modules("")
    with_foo = portable_python._inspect.get_modules("+,,foo")
    assert with_foo == base + ["foo"]

    assert portable_python._inspect.get_report(["readline", "sys", "zlib"])
    assert portable_python._inspect.represented("key", b"foo", None) == "key=foo"
    assert portable_python._inspect.represented("key", (1, 2), None) == "key=1.2"

    # Verify edge cases don't crash
    assert portable_python._inspect.module_report("foo-bar") == "*absent*"
    assert portable_python._inspect.module_representation("foo", [])
    assert not logged
