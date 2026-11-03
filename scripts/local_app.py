"""Pinned local launcher: explicit disposable target, loopback and error masking."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from scripts.migration_config import TEST_DATABASE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, choices=[TEST_DATABASE])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    environment = dict(os.environ, ILC_APP_DATABASE=args.database)
    environment["PYTHONPATH"] = str(root)
    return subprocess.call(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app/local_app.py",
            "--server.address=127.0.0.1",
            "--server.port=8501",
            "--server.headless=true",
            "--server.maxUploadSize=1",
            "--client.showErrorDetails=none",
            "--browser.gatherUsageStats=false",
        ],
        cwd=root,
        env=environment,
    )


if __name__ == "__main__":
    raise SystemExit(main())
