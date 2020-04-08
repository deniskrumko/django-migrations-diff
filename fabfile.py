from fabric.api import local, task

pypy = 'https://pypi.org'
test_pypy = 'https://test.pypi.org'

base_dir = 'django_migrations_diff'
package_name = 'django-migrtaions-diff'


# Code formatting
# ========================================================================

@task
def isort():
    """Fix imports formatting."""
    local(f'isort {base_dir} -y -rc')


@task
def pep8(path=base_dir):
    """Check PEP8 errors."""
    return local(f'flake8 --config=.flake8 {path}')


# Pipenv
# ========================================================================

@task
def lock():
    """Lock dependencies."""
    return local('pipenv lock')


@task
def install():
    """Install packages for local development."""
    return local('pipenv install --dev')


# Build & upload
# ========================================================================

@task
def clean():
    """Clean unused files before build."""
    files = (
        'build',
        'dist',
        '__pycache__',
        '.DS_Store',
        f'{base_dir}.egg-info',
        f'{base_dir}/__pycache__',
        f'{base_dir}/snapshots',
        f'{base_dir}/.DS_Store',
    )
    local('rm -rf ' + ' '.join(files))


@task
def build():
    """Build package for pypy."""
    clean()
    local('python3 setup.py sdist bdist_wheel')


@task
def pip_dev():
    """Show command how to install dev package."""
    print(
        f'pip3 install --index-url {test_pypy}/simple/ '
        f'--no-deps {package_name}'
    )


@task
def upload_to_dev():
    """Upload package to dev pypy."""
    local(
        f'python3 -m twine upload --repository-url {test_pypy}/legacy/ dist/*'
    )


@task
def upload_to_prod():
    """Upload package to real pypy."""
    local(f'python3 -m twine upload dist/*')
