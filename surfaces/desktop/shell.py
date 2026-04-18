from __future__ import annotations

import argparse
import json
from typing import Dict

from core.bootstrap.loader import boot_system


def _boot(env: str) -> Dict[str, object]:
    return boot_system(env)


def cmd_unified(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["orchestrator"].execute_workflow_document_to_presentation(
        user_id=args.user,
        surface="desktop",
        project=args.project,
        document_title=args.document_title,
        document_body=args.document_body,
        presentation_title=args.presentation_title,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Desktop unified shell")
    parser.add_argument("--env", default="runtime.env.json")
    parser.add_argument("--user", default="local-user")
    parser.add_argument("--project", required=True)
    parser.add_argument("--document-title", required=True)
    parser.add_argument("--document-body", required=True)
    parser.add_argument("--presentation-title", required=True)
    args = parser.parse_args()
    cmd_unified(args)


if __name__ == "__main__":
    main()
