import os
import shutil
import sys
from datetime import datetime
from pathlib import Path, PosixPath
from typing import Tuple


class DjangoMigrationsDiff:
    """Main class for Django Migrations Diff."""

    def __init__(self):
        """Initialize class instance."""
        self.args = sys.argv[1:]

        self._current_dir = None
        self._app_dir = None
        self._snapshots_dir = None

    def run(self):
        # Show help
        if not self.args or 'help' in self.args[0]:
            return self.show_help()

        # Show all snapshots
        if self.args[0] == 'list':
            return self.show_all_snapshots()

        # Remove snapshots
        if self.args[0] == 'rm':
            return self.remove_snapshots(*self.args[1:])

        # Create snapshot
        if len(self.args) == 1:
            return self.create_snapshot(self.args[0])

        # Compare snapshots
        return self.compare_snapshots(*self.args)

    def create_snapshot(self, name: str):
        """Create new snapshot (or update old one)."""
        new_snapshot_dir, created = self.create_snapshot_dir(name)
        total_apps, total_files = 0, 0

        for root, dirs, files in os.walk(self.current_dir):
            root = Path(root)
            if root.name == 'migrations' and files:
                destination_dir = self.create_app_migrations_dir(
                    snapshot_dir=new_snapshot_dir,
                    root=root,
                )

                for migration_name in files:
                    if migration_name != '__init__.py':
                        shutil.copyfile(
                            src=root / migration_name,
                            dst=destination_dir / migration_name,
                        )
                        total_files += 1

                total_apps += 1

        action = 'created' if created else 'updated'
        return self.print(
            f'\nSnapshot <g>{name}</g> successfully {action}:\n'
            f'  - {total_apps} applications\n'
            f'  - {total_files} migrations'
        )

    def remove_snapshots(self, *names: tuple):
        """Remove all snapshots or specific ones."""
        if not names:
            return self.print(
                '\nmdiff rm <g>all</g>\t\t-- Remove all snapshots'
                '\nmdiff rm <g><snapshot></g>\t-- Remove specific snapshots '
                '(separate names by space)'
            )

        # Remove all snapshots
        if names == ('all',):
            if not self.show_all_snapshots():
                return

            self.input(
                f'\nRemove all snapshots? Press Enter to continue...', end=''
            )
            shutil.rmtree(self.snapshots_dir)
            return self.print('<g>OK!</g>')

        # Remove specific snapshots
        self.print()
        for name in names:
            self.print(f'Snapshot {name} - ', end='')
            snapshot_dir = self.snapshots_dir / name
            if snapshot_dir.exists():
                shutil.rmtree(snapshot_dir)
                self.print(f'<g>deleted</g>')
            else:
                self.print(f'<r>not found</r>')

    def compare_snapshots(self, *names):
        print(f'compare: {names}')
        raise NotImplementedError

    def show_all_snapshots(self) -> bool:
        """Show all existing snapshots.

        Method returns True if at least one snapshot exists.

        """
        snapshots = os.listdir(self.snapshots_dir)
        if not snapshots:
            self.print('\n<r>Snapshots are not found</r>')
            return False

        spacing = max(len(max(snapshots, key=len)), 4)
        self.print(
            f'\n<g>NAME{" " * spacing}APPS\tFILES\tDATE\t\t   SIZE</g>\n'
        )
        for snapshot in snapshots:
            total_apps, total_files, total_size = 0, 0, 0
            snapshot_dir = self.snapshots_dir / snapshot
            for root, dirs, files in os.walk(snapshot_dir):
                root = Path(root)
                if files:
                    total_apps += 1
                    total_files += len(files)
                    total_size += sum(
                        (root / filename).stat().st_size
                        for filename in files
                    ) / 1000

            self.print(
                f'{snapshot}{" " * (spacing - len(snapshot) + 4)}'
                f'{total_apps}\t{total_files}\t'
                f'{self.get_created_date(snapshot_dir)}   '
                f'{int(total_size)} kB'
            )

        return True

    def show_help(self):
        print('help')
        raise NotImplementedError

    # Helpers

    @property
    def current_dir(self) -> PosixPath:
        """Directory with Django project to inspect."""
        if not self._current_dir:
            self._current_dir = Path(os.getcwd())

        return self._current_dir

    @property
    def app_dir(self) -> PosixPath:
        """Directory with django-migrations-diff app."""
        if not self._app_dir:
            self._app_dir = Path(sys.argv[0]).parent

        return self._app_dir

    @property
    def snapshots_dir(self) -> PosixPath:
        """Directory with migrations snapshots."""
        if not self._snapshots_dir:
            self._snapshots_dir = self.app_dir / 'snapshots'

            if not self._snapshots_dir.exists():
                self._snapshots_dir.mkdir()

        return self._snapshots_dir

    def create_snapshot_dir(
        self,
        name: str,
        created: bool = True,
    ) -> Tuple[PosixPath, bool]:
        """Create directory for new snapshot (and remove old one if exists.)"""
        new_snapshot_dir = self.snapshots_dir / name
        if new_snapshot_dir.exists():
            date = self.get_created_date(new_snapshot_dir)
            self.input(
                f'\nSnapshot <g>{name}</g> already exists (since {date}). '
                'Press Enter to continue...', end=''
            )
            shutil.rmtree(new_snapshot_dir)
            created = False

        new_snapshot_dir.mkdir()
        return new_snapshot_dir, created

    def create_app_migrations_dir(
        self,
        snapshot_dir: PosixPath,
        root: PosixPath,
    ) -> PosixPath:
        """Create directory for app migration files.

        Method convers path to dotted application name and creates separate
        directory in snapshot directory.

        For example:
            root = '<project>/src/apps/users/migrations'
            destination_dir = '<snapshot>/src.apps.users'

        """
        source_dir = root.relative_to(self.current_dir)
        dotted_app_name = str(source_dir.parent).replace('/', '.')

        destination_dir = snapshot_dir / dotted_app_name
        destination_dir.mkdir()
        return destination_dir

    def print(self, msg: str = '', **kwargs):
        """Print colored message in console."""
        if msg:
            colors = {
                'b': ('\x1b[34m\x1b[22m', '\x1b[39m\x1b[22m'),  # blue
                'g': ('\x1b[32m\x1b[22m', '\x1b[39m\x1b[22m'),  # green
                'r': ('\x1b[31m\x1b[22m', '\x1b[39m\x1b[22m'),  # red
                'y': ('\x1b[33m\x1b[22m', '\x1b[39m\x1b[22m'),  # yellow
            }

            for name, data in colors.items():
                msg = msg.replace(f'<{name}>', data[0])
                msg = msg.replace(f'</{name}>', data[1])

        print(msg, **kwargs)

    def input(self, msg: str, **kwargs):
        """Print colored message and ask input."""
        self.print(msg, **kwargs)
        try:
            return input()
        except KeyboardInterrupt:
            self.print('\n\n<r>Operation cancelled</r>')
            return exit()

    def get_created_date(
        self,
        path: PosixPath,
        date_format='%d.%m.%Y %H:%M',
    ) -> str:
        """Get date and time whenfile/directory was created."""
        date = datetime.fromtimestamp(path.stat().st_ctime)
        return date.strftime(date_format)


def main():
    DjangoMigrationsDiff().run()


if __name__ == '__main__':
    main()
