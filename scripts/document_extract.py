"""P01 CLI restricted to the existing disposable case database."""

import argparse
import json

from scripts.migration_config import test_engine
from src.documents.parser import DocumentError
from src.documents.service import extract_document


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--database", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--envelope", required=True)
    args = p.parse_args()
    engine = None
    try:
        from pathlib import Path

        envelope = json.loads(Path(args.envelope).read_text(encoding="utf-8"))
        engine = test_engine(args.database)
        report = extract_document(engine, args.file, envelope)
        print(json.dumps(report, default=str))
        return 0 if report["status"] == "SUCCEEDED" else 1
    except (DocumentError, ValueError, OSError):
        print(
            json.dumps(
                {"status": "FAILED", "error_category": "CONFIGURATION_OR_STORAGE_ERROR"}
            )
        )
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
