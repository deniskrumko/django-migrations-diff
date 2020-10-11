import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from filecmp import dircmp
from pathlib import Path, PosixPath
from typing import List, Optional, Set, Tuple

from . import get_version


class DjangoMigrationsDiff:
    """Main class for Django Migrations Diff."""

    package_name = 'django-migrations-diff'

    def __init__(self):
        """Initialize class instance."""
        self.args = sys.argv[1:]
        self.empty = '---'
        self.app_title = 'APPLICATION'
        self.time_format = '%d.%m.%Y %H:%M'
        self.names = []

        self.version = get_version()

        self._current_dir = None
        self._app_dir = None
        self._snapshots_dir = None
        self._last_check_file = None

        self._comparison = None
        self._apps = None
        self._spacing = None

        self._number_only = False

    def run(self):
        """Run application."""

        # "Numbers only" keyword argument
        if '--number' in self.args:
            self._number_only = True
            self.args.remove('--number')

        # Show help
        if not self.args or 'help' in self.args[0]:
            return self.show_help()

        # Show all snapshots
        if self.args[0] == 'list':
            return self.show_all_snapshots()

        # Remove snapshots
        if self.args[0] == 'rm':
            return self.remove_snapshots(*self.args[1:])

        # Remove snapshots
        if self.args[0] in ('-v', '--version'):
            return self.get_version()

        # Create snapshot
        if len(self.args) == 1:
            return self.create_snapshot(self.args[0])

        # Compare snapshots
        return self.compare_snapshots(*self.args)

    def create_snapshot(self, name: str):
        """Create new snapshot (or update old one)."""
        name = self.escape_characters(name)
        new_snapshot_dir, created = None, None
        total_apps, total_files = 0, 0

        for root, dirs, files in os.walk(self.current_dir):
            root = Path(root)
            if root.name == 'migrations' and files:
                if not new_snapshot_dir:
                    new_snapshot_dir, created = self.create_snapshot_dir(name)

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

        if not total_files:
            return self.print(f'\n<r>Can\'t find any migration in {self.current_dir}</r>')

        action = 'created' if created else 'updated'
        return self.print(
            f'\nSnapshot <g>{name}</g> successfully {action}:\n'
            f'  - {total_apps} applications\n'
            f'  - {total_files} migrations',
        )

    def remove_snapshots(self, *names: Tuple[str, ...]):
        """Remove all snapshots or specific ones."""
        if not names:
            return self.print(
                '\nmdiff rm <g>all</g>\t\t-- Remove all snapshots'
                '\nmdiff rm <g><snapshot></g>\t-- Remove specific snapshots '
                '(separate names by space)',
            )

        # Remove all snapshots
        if names == ('all',):
            if not self.show_all_snapshots():
                return

            self.input('\nRemove all snapshots? Press Enter to continue...', end='')
            shutil.rmtree(self.snapshots_dir)
            return self.print('<g>OK!</g>')

        # Remove specific snapshots
        self.print()
        names = tuple(self.escape_characters(n) for n in names)
        for name in names:
            self.print(f'Snapshot {name} - ', end='')
            snapshot_dir = self.snapshots_dir / name
            if snapshot_dir.exists():
                shutil.rmtree(snapshot_dir)
                self.print('<g>deleted</g>')
            else:
                self.print('<r>not found</r>')

    def compare_snapshots(self, *names: Tuple[str, ...]):
        """Compare migrations between several snapshots."""
        self.names = tuple(self.escape_characters(n) for n in names)
        if len(self.names) > 2:
            # NOTE: maybe it's not needed to anyone?
            return self.print('\n<r>Sorry, only 2 snapshots can be compared yet</r>')

        if self._number_only:
            return print(len(self.comparison))

        if not self.comparison:
            return self.print(
                f'\nSnapshots <g>{self.names[0]}</g> and '
                f'<g>{self.names[1]}</g> are equal!',
            )

        self.print_line(left='┌', delimiter='┬', right='┐')
        self.print_line(
            self.app_title,
            *[n.upper() for n in self.names],
            wraps=['B'] * 3,
        )

        for app, files in self.comparison.items():
            self.print_line(left='├', delimiter='┼', right='┤')
            for index, filenames in enumerate(sorted(
                files,
                key=lambda x: x[0] if x[0] != self.empty else x[1],
            )):
                wraps = [None]  # app name is not wrapped
                if filenames[0] == filenames[1]:
                    wraps += ['y', 'y']  # same filenames colored as yellow
                else:
                    for name in filenames:
                        wraps.append('r' if name == self.empty else 'g')
                self.print_line('' if index else app, *filenames, wraps=wraps)

        self.print_line(left='└', delimiter='┴', right='┘')

    def show_all_snapshots(self) -> bool:
        """Show all existing snapshots.

        Method returns True if at least one snapshot exists.

        """
        snapshots = os.listdir(self.snapshots_dir)
        if not snapshots:
            self.print('\n<r>Snapshots are not found</r>')
            return False

        spacing = max(len(max(snapshots, key=len)), 4)
        self.print(f'\n<g>NAME{" " * spacing}APPS\tFILES\tDATE\t\t   SIZE</g>\n')
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
                    )

            self.print(
                f'{snapshot}{" " * (spacing - len(snapshot) + 4)}'
                f'{total_apps}\t{total_files}\t'
                f'{self.get_created_date(snapshot_dir)}   '
                f'{self.format_total_size(total_size)}',
            )

        return True

    def show_help(self):
        """Show help for CLI."""
        from .help_text import HELP

        self.print(HELP)

    def get_version(self):
        """Get current version."""
        self.print(f'\nCurrent version is <g>{self.version}</g>')

        # Always check actual version on this command
        actual_version = self.get_actual_version()
        if not actual_version:
            self.print('\n<r>Can\'t get latest version from server</r>')
        if actual_version == self.version:
            self.print('\nThis version is <g>up-to-date</g>')

        self.set_last_check()

    def check_new_version(self):
        """Check if new version of app is available."""
        last_check = self.get_last_check()
        if last_check and (datetime.now() - last_check).seconds < 86400:
            # Do not check more than once a day
            return

        self.get_actual_version()
        self.set_last_check()

    def get_actual_version(self) -> Optional[str]:
        """Get actual version of app."""
        actual_version = None

        try:
            import requests
        except (ModuleNotFoundError, ImportError):
            self.print('\n<r>Package "requests" is not found. Cannot get actual version.</r>')
            exit()

        try:
            response = requests.get(f'https://pypi.org/pypi/{self.package_name}/json/', timeout=10)
            if response and response.status_code == 200:
                data = response.json()
                actual_version = data['info']['version']
        except Exception:
            pass

        if actual_version and actual_version != self.version:
            msg = (
                f'New version {actual_version} is available! '
                'Run this command to upgrade:'
            )
            self._spacing = [len(msg) + 1]
            self.print_line(left='\n┌', delimiter='┬', right='┐')
            self.print_line(msg, wraps=['y'])
            self.print_line(f'pip3 install --upgrade {self.package_name}', wraps=['y'])
            self.print_line(left='└', delimiter='┴', right='┘')

        return actual_version

    def get_last_check(self) -> Optional[datetime]:
        """Get time of last version check."""
        try:
            with open(self.last_check_file, 'r') as f:
                line = f.readline().strip()

            return datetime.strptime(line, self.time_format)
        except Exception:
            pass

    def set_last_check(self):
        """Set time of last version check."""
        try:
            last_check = datetime.now().strftime(self.time_format)
            with open(self.last_check_file, 'w') as f:
                f.write(last_check)
        except Exception:
            pass

    # Helpers

    def escape_characters(self, value: str) -> str:
        """Remove restricted characters from value."""
        return value.replace('/', '-')

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

    @property
    def last_check_file(self) -> PosixPath:
        """File with datetime of last version check.."""
        if not self._last_check_file:
            self._last_check_file = self.app_dir / 'last_check.mdiff'

            if not self._last_check_file.exists():
                self._snapshots_dir.touch()

        return self._last_check_file

    @property
    def comparison(self) -> dict:
        """Get comparison between two snapshots.

        Dictionary contains all apps from two snapshots. Each app contains
        pair of filenames like ('0001_initial.py', '---'), that means that
        file exists is first snapshot only.

        Pair like ('0001_initial.py', '0001_initial.py') means that files
        are different by content even they have same name.

        """
        if not self._comparison:
            self._comparison = defaultdict(list)

            for app in sorted(self.apps):
                a_dir = self.snapshots_dir / self.names[0] / app
                b_dir = self.snapshots_dir / self.names[1] / app

                if not a_dir.exists():
                    for filename in os.listdir(b_dir):
                        self._comparison[app].append((self.empty, filename))
                elif not b_dir.exists():
                    for filename in os.listdir(a_dir):
                        self._comparison[app].append((filename, self.empty))
                else:
                    compare = dircmp(a_dir, b_dir)

                    for filename in compare.left_only:
                        self._comparison[app].append((filename, self.empty))

                    for filename in compare.right_only:
                        self._comparison[app].append((self.empty, filename))

                    for filename in compare.diff_files:
                        self._comparison[app].append((filename, filename))

        return self._comparison

    @property
    def apps(self) -> Set[str]:
        """Get set of all available apps from all snapshots."""
        if not self._apps:
            self._apps = set()
            for name in self.names:
                snapshot_dir = self.snapshots_dir / name
                if not snapshot_dir.exists():
                    self.print(f'\nSnapshot <r>{name}</r> doesn\'t exist')
                    exit()

                self._apps |= set(os.listdir(snapshot_dir))

        return self._apps

    @property
    def spacing(self) -> Tuple[int, int, int]:
        """Get spacing between app name and two snapshot names.

        Method searches for longest app name and longest name for each
        snapshot. That will be used in comparison display.

        """
        if not self._spacing:
            max_app = len(self.app_title)
            max_name_1 = len(self.names[0])
            max_name_2 = len(self.names[1])

            for app, files in self.comparison.items():
                app_len = len(app)
                if app_len > max_app:
                    max_app = app_len

                for filename in files:
                    name_1, name_2 = len(filename[0]), len(filename[1])
                    if name_1 > max_name_1:
                        max_name_1 = name_1
                    if name_2 > max_name_2:
                        max_name_2 = name_2

            self._spacing = max_app + 1, max_name_1 + 1, max_name_2 + 1

        return self._spacing

    def create_snapshot_dir(
        self,
        name: str,
        created: bool = True,
    ) -> Tuple[PosixPath, bool]:
        """Create directory for new snapshot (and remove old one if exists.)"""
        new_snapshot_dir = self.snapshots_dir / name
        if new_snapshot_dir.exists():
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
            modificators = {
                'b': ('\x1b[34m\x1b[22m', '\x1b[39m\x1b[22m'),  # blue
                'g': ('\x1b[32m\x1b[22m', '\x1b[39m\x1b[22m'),  # green
                'r': ('\x1b[31m\x1b[22m', '\x1b[39m\x1b[22m'),  # red
                'y': ('\x1b[33m\x1b[22m', '\x1b[39m\x1b[22m'),  # yellow
                'B': ('\033[1m', '\033[0m'),                    # bold
                'D': ('\033[2m', '\033[0m'),                    # dim
            }

            for name, data in modificators.items():
                msg = msg.replace(f'<{name}>', data[0])
                msg = msg.replace(f'</{name}>', data[1])

        print(msg, **kwargs)

    def print_line(
        self,
        *values: Tuple[str, ...],
        wraps: Optional[List[str]] = None,
        empty: str = '─',
        left: str = '│',
        delimiter: str = '│',
        right: str = '│',
    ):
        """Print table line."""
        empty = ' ' if values else f'<D>{empty}</D>'
        self.print(f'<D>{left}</D>', end='')

        for i, spacing in enumerate(self.spacing):
            end = f'<D>{delimiter}</D>' if i + 1 != len(self.spacing) else ''
            if values:
                value = values[i]
                after_value = spacing - len(value)
                if wraps:
                    wrapper = wraps[i]
                    if wrapper:
                        value = f'<{wrapper}>{value}</{wrapper}>'
                self.print(empty + value + after_value * empty + end, end='')
            else:
                self.print(empty * (spacing + 1) + end, end='')

        self.print(f'<D>{right}</D>')

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
    ) -> str:
        """Get date and time whenfile/directory was created."""
        date = datetime.fromtimestamp(path.stat().st_ctime)
        return date.strftime(self.time_format)

    def format_total_size(self, size: int) -> str:
        """Format total snapshot size."""
        return f'{int(size / 1000)} Kb' if size > 1000 else f'{size} bytes'


def main():
    """Main function that runs application."""
    app = DjangoMigrationsDiff()
    app.run()
    app.check_new_version()


if __name__ == '__main__':
    main()
