import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from filecmp import dircmp
from pathlib import Path, PosixPath
from typing import Tuple


class DjangoMigrationsDiff:
    """Main class for Django Migrations Diff."""

    def __init__(self):
        """Initialize class instance."""
        self.args = sys.argv[1:]
        self.empty = '---'
        self.app_title = 'APPLICATION'

        self._current_dir = None
        self._app_dir = None
        self._snapshots_dir = None

        self._comparison = None
        self._apps = None
        self._spacing = None

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

    def compare_snapshots(self, *names: tuple):
        """Compare migrations between several snapshots."""
        self.names = [name.upper() for name in names]
        if len(self.names) > 2:
            # TODO: maybe it's not needed to anyone?
            return self.print(
                '\n<r>Sorry, only 2 snapshots can be compared yet</r>'
            )

        if not self.comparison:
            return self.print(
                f'\nSnapshots <g>{names[0]}</g> and <g>{names[1]}</g> '
                'are equal!'
            )

        self.print_line(left='┌', delimiter='┬', right='┐')
        self.print_line(self.app_title, *self.names, wraps=('B', 'B', 'B'))

        for app, files in self.comparison.items():
            self.print_line(left='├', delimiter='┼', right='┤')
            files = sorted(
                files,
                key=lambda x: x[0] if x[0] != self.empty else x[1]
            )
            for i, ab in enumerate(files):
                a, b = ab
                if i == 0:
                    self.print_line(app, a, b)
                else:
                    self.print_line('', a, b)

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

    @property
    def comparison(self):
        """TODO"""
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
    def apps(self):
        """TODO"""
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
    def spacing(self):
        """TODO"""
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
            date = self.get_created_date(new_snapshot_dir)
            self.input(
                f'\nSnapshot <g>{name}</g> ({date}) will be updated. '
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
        self, *values, wraps=None, left='│', empty='─', delimiter='│',
        right='│'
    ):
        """TODO"""
        if not values:
            self.print(f'<D>{left}', end='')
            for index, sp in enumerate(self.spacing):
                end = delimiter if index + 1 != len(self.spacing) else ''
                self.print(empty * sp + empty + end, end='')
            self.print(f'{right}</D>')
        else:
            # TODO: Make 1 case instead of 2
            empty = ' '
            self.print(f'<D>{left}</D>', end='')
            for index, sp in enumerate(self.spacing):
                end = (
                    f'<D>{delimiter}</D>'
                    if index + 1 != len(self.spacing) else ''
                )
                value = values[index]
                spaced = sp - len(value)
                if wraps:
                    w = wraps[index]
                    value = f'<{w}>{value}</{w}>'
                self.print(empty + value + spaced * empty + end, end='')
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
        date_format='%d.%m.%Y %H:%M',
    ) -> str:
        """Get date and time whenfile/directory was created."""
        date = datetime.fromtimestamp(path.stat().st_ctime)
        return date.strftime(date_format)


def main():
    DjangoMigrationsDiff().run()


if __name__ == '__main__':
    main()
