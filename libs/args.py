import argparse


def parse_arguments():
    """Method to describe program arguments and description.

    Returns:
        args (Namespace): object with parsed arguments.
        parser (ArgumentParser): instance of ``ArgumentParser``.

    """
    parser = argparse.ArgumentParser(
        prog='mdiff',
        description=(
            'This programs is for comparing Django migrations between '
            'two snapshots (saved migrations). At first, create new '
            'snapshot from one branch (e.g. `devevelop`) by command '
            '`mdiff dev`, then from other branch - `mdiff master`. To '
            'compare these two snapshots use command `mdiff dev master`.'
        ),
        epilog='Ⓒ 2017 Denis Krumko'
    )
    parser.add_argument(
        'snapshots',
        nargs='*',
        help='create new snapshot or compare two snapshots'
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--rm',
        nargs='*',
        help='remove snapshots (no args - remove all)'
    )
    group.add_argument(
        '-l', '--list',
        action='store_true',
        help='list all availiable snapshots'
    )
    return parser.parse_args(), parser
