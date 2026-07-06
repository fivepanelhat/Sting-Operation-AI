import bootstrap


def test_run_cmd_uses_argument_list_without_shell(monkeypatch):
    recorded = {}

    def fake_run(cmd, check, capture_output, text):
        recorded["cmd"] = cmd
        recorded["check"] = check
        recorded["capture_output"] = capture_output
        recorded["text"] = text

        class Result:
            stdout = "ok\n"

        return Result()

    monkeypatch.setattr(bootstrap.subprocess, "run", fake_run)

    stdout = bootstrap.run_cmd(["python", "-c", "print('ok')"])

    assert stdout == "ok\n"
    assert recorded == {
        "cmd": ["python", "-c", "print('ok')"],
        "check": True,
        "capture_output": True,
        "text": True,
    }


def test_install_requirements_builds_pip_command_arguments(monkeypatch):
    recorded = {}
    pip_exe = "venv/bin/pip"

    monkeypatch.setattr(bootstrap.os.path, "exists", lambda path: True)

    def fake_run_cmd(cmd, description=None):
        recorded["cmd"] = cmd
        recorded["description"] = description
        return "installed"

    monkeypatch.setattr(bootstrap, "run_cmd", fake_run_cmd)

    assert bootstrap.install_requirements(pip_exe, "requirements-dev.txt") is True
    assert recorded == {
        "cmd": [pip_exe, "install", "-r", "requirements-dev.txt"],
        "description": "Installing requirements-dev.txt",
    }
