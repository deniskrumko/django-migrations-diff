# Django Migrations Diff

Script to compare Django migrations between two snapshots.

This may be useful when you need to compare migrations in the same app between two branches.

## BASH/ZSH Alias

Add this alias `.bashrc` or `.zshrc` to easily work with script:

```bash
alias mdiff="python3 ~/<some_path>/django-migrations-diff/main.py"
```

## Available commands

* `mdiff <snapshot_name>` - create new snapshot

* `mdiff <snapshot_1> <snapshot_2>` - compare two snapshots

* `mdiff --rm` or `mdiff --rm <snapshot_1> ...` - remove all or several
  snapshots

* `mdiff -l` or `mdiff --list` - show list of all availiable snapshots

* `mdiff` or `mdiff --help` - show help

## Example of use

You Django project has two branches: `master` and `develop`.

Go to project directory and do following commands to compare migrations
between branches:

```bash

git checkout master # go to "master" branch

mdiff master # create "master" snapshot

git checkout develop # go to "develop" branch

mdiff develop # create "develop" shapshot

mdiff master develop # compare two snapshots
```

## Requirements

* **Python 3** is the only requirement for this script.

* [BeautifulTable](https://github.com/pri22296/beautifultable) already included in package (used to display tables), so you don't need to install it.

## Reason for existance

You may use not-very-normal gitflow and merging of feature branches to two
different branches may cause wrong migrations and you need to rename them or
something. Yes, this is pain. *Maybe my script will heal it a bit*...
