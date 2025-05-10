import click


@click.group(short_help="artesp_theme CLI.")
def artesp_theme():
    """artesp_theme CLI.
    """
    pass


@artesp_theme.command()
@click.argument("name", default="artesp_theme")
def command(name):
    """Docs.
    """
    click.echo("Hello, {name}!".format(name=name))


def get_commands():
    return [artesp_theme]
