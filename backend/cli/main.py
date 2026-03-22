from pathlib import Path

import typer


app = typer.Typer(help="BMI Consultant CLI")


@app.command()
def run(input: Path, backend: str = "azure") -> None:
    typer.echo(f"Scaffolded run command: input={input} backend={backend}")


@app.command()
def export(run_id: str) -> None:
    typer.echo(f"Scaffolded export command for run_id={run_id}")


if __name__ == "__main__":
    app()
