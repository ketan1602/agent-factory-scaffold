from __future__ import annotations

from pathlib import Path

import click
from harness_core import get_logger

from cli.generator import AgentGenerator
from cli.validator import ComplianceValidator

logger = get_logger(__name__)

_VALID_DOMAINS = ["retail", "finance", "healthcare", "hr"]


@click.group()
def main() -> None:
    """Agent Factory — generate production-ready LangGraph agents."""


@main.command()
@click.option("--name", required=True, help="Agent name (kebab-case, e.g. pricing-monitor)")
@click.option(
    "--domain",
    required=True,
    type=click.Choice(_VALID_DOMAINS),
    help="Domain template to use",
)
@click.option(
    "--output",
    default="generated_agents",
    show_default=True,
    help="Output directory for generated agent",
)
@click.option("--dry-run", is_flag=True, default=False, help="Render templates without disk writes")
def generate(name: str, domain: str, output: str, dry_run: bool) -> None:
    """Generate a new agent from a domain template."""
    logger.info("factory_generate_start", agent_name=name, domain=domain, dry_run=dry_run)
    gen = AgentGenerator(output_dir=Path(output))
    result = gen.generate(name, domain, dry_run=dry_run)

    click.echo(f"\nAgent: {result.agent_name} ({result.domain})")
    click.echo(f"Time:  {result.duration_seconds:.2f}s")
    click.echo(f"Mode:  {'dry-run' if dry_run else 'written'}")
    click.echo(f"Path:  {result.output_path}\n")
    click.echo("Files generated:")
    for f in result.files_generated:
        click.echo(f"  {f}")

    logger.info(
        "factory_generate_done",
        agent_name=name,
        file_count=len(result.files_generated),
        duration_seconds=result.duration_seconds,
    )


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def validate(path: Path) -> None:
    """Validate a generated agent for compliance with the 8-check standard."""
    logger.info("factory_validate_start", agent_path=str(path))
    validator = ComplianceValidator()
    result = validator.validate(path)

    click.echo(f"\nValidating: {result.agent_path}")
    click.echo(f"Pass rate: {result.pass_rate_pct:.0f}%\n")

    for check in result.checks:
        icon = "PASS" if check.passed else "FAIL"
        click.echo(f"  [{icon}] {check.name}: {check.message}")

    status = "ALL CHECKS PASSED" if result.all_passed else "SOME CHECKS FAILED"
    click.echo(f"\n{status}")
    logger.info("factory_validate_done", agent_path=str(path), all_passed=result.all_passed)


@main.command(name="list-templates")
def list_templates() -> None:
    """List available domain templates."""
    gen = AgentGenerator()
    domains = gen.available_domains()
    click.echo("\nAvailable domains:")
    for d in domains:
        click.echo(f"  {d}")
