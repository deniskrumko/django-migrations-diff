django-migrations-diff
======================

.. image:: https://img.shields.io/pypi/v/django-migrations-diff.svg
    :target: https://pypi.org/project/django-migrations-diff/
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/django-migrations-diff.svg
    :target: https://pypi.org/project/django-migrations-diff/
    :alt: Python versions

.. image:: https://img.shields.io/pypi/l/django-migrations-diff.svg
    :target: https://raw.githubusercontent.com/deniskrumko/django-migrations-diff/master/LICENSE
    :alt: License


CLI to compare Django migrations between two snapshots.

This may be useful when you need to compare migrations in the same app between different branches.

Installation
^^^^^^^^^^^^
.. code-block:: bash

    pip install django-migrations-diff

Requirements
^^^^^^^^^^^^

- Python 3.6 or higher

How to use
^^^^^^^^^^

.. code-block:: bash

    # show help
    mdiff help

    # Create migrations snapshot
    mdiff <snapshot>

    # Compare two snapshots
    mdiff <snapshot_1> <snapshot_2>

    # Compare two snapshots (get number of diffent migrations)
    mdiff <snapshot_1> <snapshot_2> --number

    # List of all snapshots
    mdiff list

    # Remove all or specific snapshots
    mdiff rm all
    mdiff rm <snapshot_1> <snapshot_2>

    # Get current version
    mdiff -v

Example
^^^^^^^

For example, you need to compare "master" and "develop" branches.

.. code-block:: bash

  git checkout master # go to "master" branch

  mdiff master # create "master" snapshot

  git checkout develop # go to "develop" branch

  mdiff develop # create "develop" shapshot

  mdiff master develop # compare two snapshots

In output you expect to see only new migrations in "develop" branch, otherwise
it means that original migrations from "master" were deleted or changed.

Yellow-labeled migration means that same migration exist in both snapshots
but it was modified and now has different code.

CI/CD configuration
^^^^^^^^^^^^^^^^^^^

This package also can be used to detect new migrations in CI/CD pipelines.
For example, following stage in **.gitlab-ci.yml** will fail if there are new migrations in current
branch in comparison to master branch.

.. code-block:: bash

  chechcheck:
    stage: tests
    script:
      - pip install django-migrations-diff==2.0.4
      - git merge-base origin/master HEAD | xargs git checkout
      - mdiff master
      - git checkout ${CI_COMMIT_REF_NAME}
      - mdiff ${CI_COMMIT_REF_NAME}
      - mdiff master ${CI_COMMIT_REF_NAME}
      - (if [[ $(mdiff master ${CI_COMMIT_REF_NAME} --number) == 0 ]]; then echo "No new migrations"; else exit 1; fi;)
    allow_failure: true

**NOTE**: This is not full stage descriptions, this is only example.
