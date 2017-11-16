import os
import shutil
import sys

from filecmp import dircmp

from libs.args import parse_arguments
from libs.console_utils import ask_yes_no
from libs.beautifultable.beautifultable import BeautifulTable
from libs.cprint import cprint, error_exit


class MigrationsDiff(object):
    """Main class for Django Migrations Diff."""

    def __init__(self, *args, **kwargs):
        """Initialization method."""
        # Current directory - django app with migrations
        self.current_dir = os.getcwd()
        # Script directory - path to this exact script
        self.script_dir = os.path.dirname(sys.argv[0])
        # Snapshots directory - path to saved migrations (snapshots)
        self.snapshots_dir = self.script_dir + '/snapshots'

        # Create snapshots directory if it doesn't exist
        if not os.path.isdir(self.snapshots_dir):
            os.mkdir(self.snapshots_dir)

        # Get all existing snapshots
        self.snapshots = os.listdir(self.snapshots_dir)

    def execute(self):
        """Main method to execute program.

        Method parser console arguments and maps actions to each argument.

        """
        args, parser = parse_arguments()

        # Create or compare snapshots
        if args.snapshots:
            # 1 - create new snapshot
            if len(args.snapshots) == 1:
                return self.create_snapshot(snapshot=args.snapshots[0])

            # 2 - compare two snapshots
            if len(args.snapshots) == 2:
                return self.compare_snapshots(*args.snapshots)

            # otherwise - error
            error_exit('Incorrect input. See help for available commands.')

        # Remove several or all snapshots
        if args.rm is not None:
            return self.remove_snapshots(snapshots=args.rm)

        # Show list of all available snapshots
        if args.list:
            return self.show_all_snapshots()

        # If no arguments - show help
        parser.print_help()

    # CREATE SNAPSHOTS

    def create_snapshot(self, snapshot):
        """Method to create new snapshot.

        Creating of snapshot includes following steps:
            - Create directory for snapshot (or remove existing one)
            - Find all "migrations" folders in project tree
            - Save migrations from these folders

        """
        self.create_snapshot_dir(snapshot)

        for root, dirs, files in os.walk(self.current_dir):
            if root[-11:] == '/migrations' and files:
                self.save_migrations(snapshot, root, files)

        cprint('Successfully created "{}" snapshot'.format(snapshot), 'green')

    def create_snapshot_dir(self, snapshot):
        """Method to create snapshot directory.

        If directory already exists - it's need to be deleted and then create
        new one.

        """
        self.curent_snapshot_dir = self.snapshots_dir + '/' + snapshot

        # If directory already exist - ask user to update it
        if os.path.isdir(self.curent_snapshot_dir):
            question = (
                'Snapshot "{}" already exists. Update it?'.format(snapshot)
            )
            if not ask_yes_no(question):
                error_exit('Snapshot is not updated')

            shutil.rmtree(self.curent_snapshot_dir)

        os.mkdir(self.curent_snapshot_dir)

    def create_destination_dir(self, source_dir):
        """Method to create destination directory.

        Method converts path to slug and creates directory with this slug:

            apps/example/migrations -> apps.example

        """
        slug = source_dir.replace('/', '.')[1:-11]
        destination_dir = self.curent_snapshot_dir + '/' + slug
        os.mkdir(destination_dir)
        return destination_dir

    def save_migrations(self, snapshot, root, files):
        """Method to save migration from source path to destination."""
        source_dir = root.replace(self.current_dir, '')
        destination_dir = self.create_destination_dir(source_dir)

        for migration_name in files:
            shutil.copyfile(
                src=os.path.join(root, migration_name),
                dst=os.path.join(destination_dir, migration_name)
            )

    def check_snapshot_exists(self, snapshot, with_exit=False):
        """Method to check if snapshot exists or not."""
        exists = snapshot in self.snapshots

        if not exists:
            cprint('Snapshot "{}" doesn\'t exist.'.format(snapshot), 'red')

            if with_exit:
                exit()

        return exists

    # COMPARE SNAPSHOTS

    def compare_snapshots(self, src, dst):
        """Method to compare two snapshots."""
        # Check that both snapshots exist
        self.check_snapshot_exists(src, with_exit=True)
        self.check_snapshot_exists(dst, with_exit=True)

        # Get directories for both snapshots
        src_snapshot_dir = os.path.join(self.snapshots_dir, src)
        dst_snapshot_dir = os.path.join(self.snapshots_dir, dst)

        # Get migrations from both snapshots
        src_migrations = set(os.listdir(src_snapshot_dir))
        dst_migrations = set(os.listdir(dst_snapshot_dir))

        # Get migrations for src/dst only and for both
        src_migrations_only = src_migrations - dst_migrations
        dst_migrations_only = dst_migrations - src_migrations
        both_migrations = src_migrations & dst_migrations

        snapshots_are_equal = True

        table = BeautifulTable()
        table.column_headers = [
            'APPLICATION', 'MIGRATIONS', src.upper(), dst.upper()
        ]

        # If src has unique migration directory
        if src_migrations_only:
            snapshots_are_equal = False
            for folder in src_migrations_only:
                table.append_row([folder, 'All files', '+', ''])

        # If dst has unique migration directory
        if dst_migrations_only:
            snapshots_are_equal = False
            for folder in dst_migrations_only:
                table.append_row([folder, 'All files', '', '+'])

        # If src and dst has mutual directories - compare files inside them
        if both_migrations:
            for migration in both_migrations:
                src_migrations_dir = os.path.join(src_snapshot_dir, migration)
                dst_migrations_dir = os.path.join(dst_snapshot_dir, migration)

                # Compare directories for same app between snapshots
                compare = dircmp(src_migrations_dir, dst_migrations_dir)

                if any([
                    compare.diff_files, compare.left_only, compare.right_only
                ]):
                    snapshots_are_equal = False

                if compare.left_only:
                    snapshots_are_equal = False
                    for f in compare.left_only:
                        table.append_row([migration, f, '+', ''])

                if compare.right_only:
                    snapshots_are_equal = False
                    for f in compare.right_only:
                        table.append_row([migration, f, '', '+'])

                if compare.diff_files:
                    snapshots_are_equal = False
                    for f in compare.diff_files:
                        table.append_row([migration, f, '?', '?'])

        if snapshots_are_equal:
            cprint('Snapshots are equal!', 'green')
        else:
            print(table)

    # REMOVE SNAPSHOTS

    def remove_snapshots(self, snapshots):
        """Method to delete snapshots."""
        # Delete several snapshots
        if snapshots:
            for snapshot in snapshots:
                if self.check_snapshot_exists(snapshot):
                    question = 'Remove snapshot "{}"?'.format(snapshot)
                    if ask_yes_no(question):
                        shutil.rmtree(
                            os.path.join(self.snapshots_dir, snapshot)
                        )
                        cprint('Snapshot is deleted', 'green')

        # Remove all snapshots
        else:
            self.show_all_snapshots()

            if self.snapshots and ask_yes_no('Remove all snapshots?'):
                shutil.rmtree(self.snapshots_dir)
                cprint('All snapshots are deleted', 'green')

    # SHOW SNAPSHOTS

    def show_all_snapshots(self):
        """Method to show all snapshots."""
        if not self.snapshots:
            error_exit('There are no available snapshots')

        cprint('All available snapshots:\n')
        for snapshot in self.snapshots:
            print('    · {}'.format(snapshot))


if __name__ == '__main__':
    MigrationsDiff().execute()
