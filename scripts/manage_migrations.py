"""
Helper CLI to run Flask-Migrate commands without relying on the external flask CLI.

Usage:
    python scripts/manage_migrations.py init
    python scripts/manage_migrations.py migrate -m "message"
    python scripts/manage_migrations.py upgrade
    python scripts/manage_migrations.py revision -m "message"
    python scripts/manage_migrations.py stamp head

This uses the Flask-Migrate functions directly, operating on the app returned by create_app().
"""
import sys
import click
from app import create_app, db
import flask_migrate

app = create_app()

@click.group()
def cli():
    pass

@cli.command()
def init():
    """Create a new migrations directory (equivalent to `flask db init`)."""
    with app.app_context():
        flask_migrate.init(directory='migrations')
        print('migrations directory initialized')

@cli.command()
@click.option('-m', '--message', default='auto migration', help='Migration message')
def migrate(message):
    """Generate a new migration script (equivalent to `flask db migrate`)."""
    with app.app_context():
        flask_migrate.migrate(message=message)
        print('migration script generated')

@cli.command()
def upgrade():
    """Apply migrations (equivalent to `flask db upgrade`)."""
    with app.app_context():
        flask_migrate.upgrade()
        print('database upgraded')

@cli.command()
@click.option('-m', '--message', default='revision', help='Revision message')
def revision(message):
    """Create an empty revision (equivalent to `flask db revision`)."""
    with app.app_context():
        flask_migrate.revision(message=message)
        print('revision created')

@cli.command()
@click.argument('version', required=False)
def stamp(version):
    """Stamp the revision (equivalent to `flask db stamp`)."""
    with app.app_context():
        if version:
            flask_migrate.stamp(revision=version)
            print(f'stamped revision {version}')
        else:
            flask_migrate.stamp()
            print('stamped current database')

if __name__ == '__main__':
    cli()
