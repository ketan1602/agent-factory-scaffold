from __future__ import annotations

import os
from pathlib import Path

import click

from cli.generator import AgentGenerator
from cli.manifest import load_manifest, load_manifests
from cli.online import online_report
from cli.release import release
from cli.validator import ComplianceValidator


@click.group()
def main() -> None:
    """Agent Factory: stamp out manifest-driven agents with harness, eval and release gates."""


@main.command()
@click.option("--manifest", "manifest_path", required=True,
              type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--output", default="generated_agents", show_default=True,
              type=click.Path(file_okay=False, path_type=Path))
@click.option("--dry-run", is_flag=True, help="List the files without writing them")
def generate(manifest_path: Path, output: Path, dry_run: bool) -> None:
    """Generate one agent from its manifest."""
    result = AgentGenerator(output_dir=output).generate(load_manifest(manifest_path), dry_run)
    click.echo(f"Agent: {result.agent_name}")
    click.echo(f"Time:  {result.duration_seconds:.3f}s")
    click.echo(f"Mode:  {'dry-run' if dry_run else 'written'} to {result.output_path}")
    for rel in result.files_generated:
        click.echo(f"  {rel}")


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
def validate(path: Path) -> None:
    """Run the compliance checks against a generated agent."""
    result = ComplianceValidator().validate(path)
    for check in result.checks:
        click.echo(f"  [{'PASS' if check.passed else 'FAIL'}] {check.name}: {check.message}")
    click.echo("ALL CHECKS PASSED" if result.all_passed else "SOME CHECKS FAILED")
    if not result.all_passed:
        raise SystemExit(1)


@main.command(name="release")
@click.option("--manifests", "manifest_dir", default="manifests", show_default=True,
              type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--output", default="generated_agents", show_default=True,
              type=click.Path(file_okay=False, path_type=Path))
@click.option("--report", default="measurements/release.json", show_default=True,
              type=click.Path(dir_okay=False, path_type=Path))
def release_cmd(manifest_dir: Path, output: Path, report: Path) -> None:
    """Generate every manifest's agent, run its live eval, apply its gate, and record cost."""
    try:
        data = release(load_manifests(manifest_dir), output, report, os.environ)
    except OSError as exc:
        raise click.ClickException(str(exc)) from exc
    for agent in data["agents"]:
        gate = "BLOCKED" if agent["gate"]["blocked"] else "RELEASED"
        click.echo(f"{agent['agent']:<14} {agent['cases_passed']}/{agent['cases_total']} passed  "
                   f"gate {gate}  compliance {agent['compliance_checks_passed']}/"
                   f"{agent['compliance_checks_total']}")
        for reason in agent["gate"]["reasons"]:
            click.echo(f"               - {reason}")
    summary = data["summary"]
    click.echo(f"Released {summary['agents_released']}/{summary['agents_total']} agents; "
               f"cost per successful outcome: {summary['cost_per_successful_outcome_usd']}")
    click.echo(f"Wrote {report}")
    if summary["agents_blocked"]:
        raise SystemExit(1)



@main.command(name="online")
@click.option("--generated", "generated_root", default="generated_agents", show_default=True,
              type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--report", default="measurements/online.json", show_default=True,
              type=click.Path(dir_okay=False, path_type=Path))
def online_cmd(generated_root: Path, report: Path) -> None:
    """Check recorded runs for refund intents the guard should have caught."""
    data = online_report(generated_root, report)
    for name, agent in data["agents"].items():
        click.echo(f"{name:<14} intents {agent['refund_intents']}  "
                   f"escalated {agent['guard_escalations']}  "
                   f"silent misses {agent['silent_misses']}")
    click.echo(f"Wrote {report}")
    if data["summary"]["alert"]:
        click.echo("ALERT: refund requests reached completion without a refund or escalation")
        raise SystemExit(1)
