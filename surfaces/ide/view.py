from __future__ import annotations

import argparse
import json
from typing import Dict

from core.bootstrap.loader import boot_system


def _boot(env: str) -> Dict[str, object]:
    return boot_system(env)


def main() -> None:
    parser = argparse.ArgumentParser(description="IDE surface context view")
    parser.add_argument("--env", default="runtime.env.json")
    parser.add_argument("--user", default="local-user")
    parser.add_argument("--project", required=True)
    args = parser.parse_args()

    system = _boot(args.env)
    result = system["orchestrator"].retrieve_context(user_id=args.user, project=args.project)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
