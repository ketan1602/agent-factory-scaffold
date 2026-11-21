from __future__ import annotations

from pathlib import Path

import click

from cli.generator import AgentGenerator
from cli.measure import measure as run_measure
from cli.validator import ComplianceValidator


@click.group()
def main() -> None:
    """Agent Factory: stamp out the support agent with harness, eval and compliance wired in."""


@main.command()
@click.option("--name", required=True, help="Agent name, lowercase kebab-case (e.g. support-east)")
@click.option("--output", default="generated_agents", show_default=True,
              type=click.Path(file_okay=False, path_type=Path))
@click.option("--dry-run", is_flag=True, help="List the files without writing them")
def generate(name: str, output: Path, dry_run: bool) -> None:
    """Generate a support agent project."""
    try:
        result = AgentGenerator(output_dir=output).generate(name, dry_run=dry_run)
    except ValueError as exc:
        raise click.BadParameter(str(exc), param_hint="--name") from exc
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


@main.command()
@click.option("--name", required=True, help="Agent name to generate and evaluate")
@click.option("--output", default="generated_agents", show_default=True,
              type=click.Path(file_okay=False, path_type=Path))
@click.option("--report", default="measurements/factory_performance.json", show_default=True,
              type=click.Path(dir_okay=False, path_type=Path))
def measure(name: str, output: Path, report: Path) -> None:
    """Generate the agent, run its live eval, and write the measured timings."""
    try:
        data = run_measure(name, output, report)
    except ValueError as exc:
        raise click.BadParameter(str(exc), param_hint="--name") from exc
    click.echo(f"Model:            {data['model']}")
    click.echo(f"Time to eval:     {data['time_to_eval_minutes']} min")
    click.echo(f"Cases passed:     {data['cases_passed']}/{data['cases_total']}")
    checks = f"{data['compliance_checks_passed']}/{data['compliance_checks_total']}"
    click.echo(f"Compliance:       {checks}")
    click.echo(f"Wrote {report}")
