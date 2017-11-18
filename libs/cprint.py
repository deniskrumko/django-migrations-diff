__all__ = ('color_msg', 'cprint', 'error_exit')


def color_msg(msg, color):
    """Function to get colored image."""
    color_map = {
        'red': 91,
        'green': 92,
        'yellow': 93,
        'blue': 94,
    }
    return '\033[{0}m{1}\033[00m'.format(color_map[color], msg)


def cprint(msg, color=None):
    """Method to do colored print."""
    print('\n  {}'.format(color_msg(msg, color) if color else msg))


def error_exit(msg):
    """Shortcut to exit and show red message."""
    exit('\n  {}'.format(color_msg(msg, 'red')))
