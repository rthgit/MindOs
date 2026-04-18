from __future__ import annotations

import argparse
import json
import time
from typing import Dict

from core.bootstrap.loader import boot_system


def _boot(env: str) -> Dict[str, object]:
    return boot_system(env)


def cmd_run(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["orchestrator"].execute_intent(
        {
            "user_id": args.user,
            "surface": "cli",
            "project": args.project,
            "action": "generate_document",
            "requested_capability": "document.generate",
            "payload": {
                "title": args.title,
                "body": args.body,
            },
        },
        require_confirmation=args.confirm,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_retrieve(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["orchestrator"].retrieve_context(user_id=args.user, project=args.project)
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_resume(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["orchestrator"].resume_run(run_id=args.run_id)
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_rollback(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["orchestrator"].rollback_internal(run_id=args.run_id)
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_promote(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    definition = {
        "project": args.project,
        "surface_origin": "cli",
        "action": "generate_document",
        "requested_capability": "document.generate",
        "template": {"title": args.title, "body": args.body},
    }
    system["orchestrator"].promote_to_procedural_memory(pattern_id=args.pattern_id, definition=definition)
    print(json.dumps({"pattern_id": args.pattern_id, "status": "saved"}, indent=2, sort_keys=True))


def cmd_run_pattern(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    overrides = {}
    if args.title:
        overrides["title"] = args.title
    if args.body:
        overrides["body"] = args.body
    result = system["orchestrator"].run_procedural_pattern(
        pattern_id=args.pattern_id,
        user_id=args.user,
        surface="cli",
        overrides=overrides,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_run_presentation(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    document_text = args.source_document
    if args.from_latest:
        ctx = system["orchestrator"].retrieve_context(user_id=args.user, project=args.project)
        latest_run = ctx.get("latest_run") or {}
        output = latest_run.get("output") or {}
        document_text = output.get("artifact", document_text)
    result = system["orchestrator"].execute_intent(
        {
            "user_id": args.user,
            "surface": "cli",
            "project": args.project,
            "action": "generate_presentation",
            "requested_capability": "presentation.generate",
            "payload": {
                "title": args.title,
                "source_document": document_text,
            },
        }
    )
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_run_workflow(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["orchestrator"].execute_workflow_document_to_presentation(
        user_id=args.user,
        surface="cli",
        project=args.project,
        document_title=args.document_title,
        document_body=args.document_body,
        presentation_title=args.presentation_title,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_create_schedule(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["orchestrator"].create_schedule(
        schedule_id=args.schedule_id,
        pattern_id=args.pattern_id,
        user_id=args.user,
        surface=args.surface,
        interval_seconds=args.interval_seconds,
        start_at_epoch=args.start_at_epoch,
        max_runs=args.max_runs,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_tick_scheduler(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    now_epoch = args.now_epoch if args.now_epoch is not None else int(time.time())
    result = system["orchestrator"].run_scheduler_tick(now_epoch=now_epoch)
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_list_schedules(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["orchestrator"].list_schedules()
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_plugin_install(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["plugin_manager"].install(args.plugin_id)
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_plugin_list(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["plugin_manager"].list_installed()
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_plugin_remove(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["plugin_manager"].remove(args.plugin_id)
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_plugin_upgrade(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["plugin_manager"].upgrade(args.plugin_id)
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_plugin_catalog(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = {"catalog": system["plugin_manager"].list_catalog()}
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_program_catalog(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = {"program_catalog": system["plugin_manager"].list_program_catalog()}
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_program_install(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["plugin_manager"].install_program(
        plugin_id=args.program_id,
        execute_install=args.execute_install,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_program_upgrade(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["plugin_manager"].upgrade(args.program_id)
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_program_remove(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    result = system["plugin_manager"].remove(args.program_id)
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_program_list(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    installed = system["plugin_manager"].list_installed()
    program_rows = {k: v for k, v in installed.items() if v.get("kind") == "program"}
    print(json.dumps(program_rows, indent=2, sort_keys=True))


def cmd_program_run(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    payload = {
        "args": list(args.arg or []),
        "dry_run": args.dry_run,
        "timeout_sec": args.timeout_sec,
    }
    result = system["orchestrator"].execute_intent(
        {
            "user_id": args.user,
            "surface": "cli",
            "project": args.project,
            "action": "execute_program",
            "requested_capability": args.capability,
            "payload": payload,
        }
    )
    print(json.dumps(result, indent=2, sort_keys=True))


def cmd_llm_health(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    provider = system.get("llm_provider")
    if provider is None:
        print(json.dumps({"enabled": False, "status": "disabled"}, indent=2, sort_keys=True))
        return
    out = provider.health()
    out["enabled"] = True
    print(json.dumps(out, indent=2, sort_keys=True))


def cmd_llm_generate(args: argparse.Namespace) -> None:
    system = _boot(args.env)
    provider = system.get("llm_provider")
    if provider is None:
        raise RuntimeError("LLM provider disabled in runtime.env.json")
    from core.llm.base import LLMRequest

    out = provider.generate(
        LLMRequest(
            prompt=args.prompt,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
    )
    print(
        json.dumps(
            {"provider": out.provider, "model": out.model, "text": out.text},
            indent=2,
            sort_keys=True,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI-native OS CLI surface")
    parser.add_argument("--env", default="runtime.env.json")
    parser.add_argument("--user", default="local-user")
    sub = parser.add_subparsers(required=True)

    run = sub.add_parser("run")
    run.add_argument("--project", required=True)
    run.add_argument("--title", required=True)
    run.add_argument("--body", required=True)
    run.add_argument("--confirm", action="store_true")
    run.set_defaults(func=cmd_run)

    retrieve = sub.add_parser("retrieve")
    retrieve.add_argument("--project", required=True)
    retrieve.set_defaults(func=cmd_retrieve)

    resume = sub.add_parser("resume")
    resume.add_argument("--run-id", required=True)
    resume.set_defaults(func=cmd_resume)

    rollback = sub.add_parser("rollback")
    rollback.add_argument("--run-id", required=True)
    rollback.set_defaults(func=cmd_rollback)

    promote = sub.add_parser("promote")
    promote.add_argument("--project", required=True)
    promote.add_argument("--pattern-id", required=True)
    promote.add_argument("--title", required=True)
    promote.add_argument("--body", required=True)
    promote.set_defaults(func=cmd_promote)

    run_pattern = sub.add_parser("run-pattern")
    run_pattern.add_argument("--pattern-id", required=True)
    run_pattern.add_argument("--title")
    run_pattern.add_argument("--body")
    run_pattern.set_defaults(func=cmd_run_pattern)

    presentation = sub.add_parser("run-presentation")
    presentation.add_argument("--project", required=True)
    presentation.add_argument("--title", required=True)
    presentation.add_argument("--source-document", default="")
    presentation.add_argument("--from-latest", action="store_true")
    presentation.set_defaults(func=cmd_run_presentation)

    workflow = sub.add_parser("run-workflow")
    workflow.add_argument("--project", required=True)
    workflow.add_argument("--document-title", required=True)
    workflow.add_argument("--document-body", required=True)
    workflow.add_argument("--presentation-title", required=True)
    workflow.set_defaults(func=cmd_run_workflow)

    create_schedule = sub.add_parser("create-schedule")
    create_schedule.add_argument("--schedule-id", required=True)
    create_schedule.add_argument("--pattern-id", required=True)
    create_schedule.add_argument("--interval-seconds", required=True, type=int)
    create_schedule.add_argument("--surface", default="cli")
    create_schedule.add_argument("--start-at-epoch", type=int)
    create_schedule.add_argument("--max-runs", type=int)
    create_schedule.set_defaults(func=cmd_create_schedule)

    tick_scheduler = sub.add_parser("tick-scheduler")
    tick_scheduler.add_argument("--now-epoch", type=int)
    tick_scheduler.set_defaults(func=cmd_tick_scheduler)

    list_schedules = sub.add_parser("list-schedules")
    list_schedules.set_defaults(func=cmd_list_schedules)

    plugin_install = sub.add_parser("plugin-install")
    plugin_install.add_argument("--plugin-id", required=True)
    plugin_install.set_defaults(func=cmd_plugin_install)

    plugin_list = sub.add_parser("plugin-list")
    plugin_list.set_defaults(func=cmd_plugin_list)

    plugin_remove = sub.add_parser("plugin-remove")
    plugin_remove.add_argument("--plugin-id", required=True)
    plugin_remove.set_defaults(func=cmd_plugin_remove)

    plugin_upgrade = sub.add_parser("plugin-upgrade")
    plugin_upgrade.add_argument("--plugin-id", required=True)
    plugin_upgrade.set_defaults(func=cmd_plugin_upgrade)

    plugin_catalog = sub.add_parser("plugin-catalog")
    plugin_catalog.set_defaults(func=cmd_plugin_catalog)

    program_catalog = sub.add_parser("program-catalog")
    program_catalog.set_defaults(func=cmd_program_catalog)

    program_install = sub.add_parser("program-install")
    program_install.add_argument("--program-id", required=True)
    program_install.add_argument("--execute-install", action="store_true")
    program_install.set_defaults(func=cmd_program_install)

    program_upgrade = sub.add_parser("program-upgrade")
    program_upgrade.add_argument("--program-id", required=True)
    program_upgrade.set_defaults(func=cmd_program_upgrade)

    program_remove = sub.add_parser("program-remove")
    program_remove.add_argument("--program-id", required=True)
    program_remove.set_defaults(func=cmd_program_remove)

    program_list = sub.add_parser("program-list")
    program_list.set_defaults(func=cmd_program_list)

    program_run = sub.add_parser("program-run")
    program_run.add_argument("--project", required=True)
    program_run.add_argument("--capability", required=True)
    program_run.add_argument("--arg", action="append")
    program_run.add_argument("--timeout-sec", type=int, default=30)
    program_run.add_argument("--dry-run", action="store_true")
    program_run.set_defaults(func=cmd_program_run)

    llm_health = sub.add_parser("llm-health")
    llm_health.set_defaults(func=cmd_llm_health)

    llm_generate = sub.add_parser("llm-generate")
    llm_generate.add_argument("--prompt", required=True)
    llm_generate.add_argument("--temperature", type=float, default=0.0)
    llm_generate.add_argument("--max-tokens", type=int, default=120)
    llm_generate.set_defaults(func=cmd_llm_generate)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
