import typer

app = typer.Typer(no_args_is_help=True)

@app.command()
def hello(name: str):
    print(f"Hello {name}")

@app.command()
def goodbye():
    print("Goodbye")

