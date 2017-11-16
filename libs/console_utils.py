def ask_yes_no(question):
    """Method to ask question to user than he must answer yes/no.

    Example:

        Do you like playing Dark Souls 3? [Y/n]

    """
    while True:
        answer = input('\n  {} [Y/n] '.format(question))

        if answer in ['', 'y', 'Y']:
            return True

        if answer in ['n', 'N']:
            return False

        print('Incorrect answer.')
