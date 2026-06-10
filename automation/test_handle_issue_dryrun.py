from automation.handle_issue import main
import sys
import json
from pathlib import Path


def test_handle_issue_dry_run(tmp_path, monkeypatch, capsys):
    # write a sample event
    event = {
        "action": "labeled",
        "issue": {
            "number": 999,
            "title": "Provision Docker dev",
            "body": "Please provision docker dev for alice",
            "user": {"login": "alice"},
            "labels": [{"name": "auto-provision"}],
        },
        "label": {"name": "auto-provision"},
    }
    path = tmp_path / "event.json"
    path.write_text(json.dumps(event), encoding="utf-8")

    # set args to point to our event and enable dry-run
    monkeypatch.setattr(sys, "argv", ["handle_issue.py", "--event-path", str(path), "--dry-run"])

    # run main — should exit cleanly and print generated files
    main()
    captured = capsys.readouterr()
    assert "Dry run enabled" in captured.out
    assert "Generated files:" in captured.out
