from functools32 import lru_cache
from github3 import login
from sarge import run, Capture
import click
import os


import logging
logger = logging.getLogger(__name__)


@lru_cache()
def _github_login(token):
    message = 'Authenticating with token...'

    if _get_token_from_file():
        message = 'Authenticating with token from githuber.token file...'

    click.echo(message)
    github = login(token=token)
    return github


@lru_cache()
def _get_repos(github, org_name=None, username=None):
    repositories = None

    if org_name:
        click.echo('Get the {0} organization...'.format(org_name))
        organization = github.organization(org_name)

        click.echo('Get repositories for the {0} organization...'.format(org_name))
        repositories = organization.repositories()
    elif username:
        click.echo('Get repositories for the {0} user...'.format(username))
        repositories = github.repositories_by(username)
    else:
        raise Exception('No organization or username to get repositories for')

    return repositories


def _update_existing_repos(subdirectory, repo_names, directory_names):
    errors = []
    existing_repo_names = [val for val in directory_names if val in set(repo_names)]

    if existing_repo_names:
        progressbar_length = len(existing_repo_names)

        with click.progressbar(existing_repo_names, length=progressbar_length, label='Update existing repos:') as repos:
            for repo_name in repos:
                cwd = os.path.join(subdirectory, repo_name)
                r = run('git pull origin master', cwd=cwd, stdout=Capture(), stderr=Capture())

                if r.returncode:
                    errors.append('Pulling {0} failed with: {1}'.format(cwd, r.stderr.text))

    return errors


def _retrieve_new_repos(subdirectory, repositories, repo_names, directory_names):
    errors = []
    new_repo_names = [val for val in repo_names if val not in set(directory_names)]

    if new_repo_names:
        progressbar_length = len(new_repo_names)

        with click.progressbar(new_repo_names, length=progressbar_length, label='Retrieve new repos:') as repos:
            for repo_name in repos:
                git_url = None
                matched_repos = filter(lambda r: r.name == repo_name, repositories)

                if matched_repos and matched_repos[0]:
                    git_url = matched_repos[0].git_url
                    git_url = git_url.replace('git://github.com/', 'git@github.com:')
                    cwd = subdirectory
                    r = run('git clone {0}'.format(git_url), cwd=cwd, stdout=Capture(), stderr=Capture())

                    if r.returncode:
                        errors.append('Cloning {0} failed with: {1}'.format(git_url, r.stderr.text))

    return errors


def update_and_retrieve_repos(repositories, subdirectory):
    repo_names = _get_repo_names(repositories)
    directory_names = _get_directory_names(subdirectory)

    errors = []
    errors.extend(_update_existing_repos(subdirectory, repo_names, directory_names))
    errors.extend(_retrieve_new_repos(subdirectory, repositories, repo_names, directory_names))

    for error in errors:
        click.echo(error)

    for directory_name in directory_names:
        if directory_name not in repo_names:
            click.echo('Directory {0} is not in the list of repos'.format(directory_name))


def _get_directory_names(subdirectory):
    if not os.path.isdir(subdirectory):
        os.mkdir(subdirectory)

    directory_names = [d for d in os.listdir(subdirectory) if os.path.isdir(os.path.join(subdirectory, d)) and not d.startswith('.')]
    return directory_names


def get_commit_count(subdirectory, repo_names, commits_year=None, commits_month=None, commits_day=None):
    commits_count = 0
    commits_since = None
    commits_until = None

    if commits_year:
        commits_since = '01/01/{0}'.format(commits_year)
        commits_until = '12/31/{0}'.format(commits_year)
    elif commits_month:
        raise Exception('commits_month functionality not implemented')
    elif commits_day:
        raise Exception('commits_day functionality not implemented')
    else:
        raise Exception('Not implemented')

    progressbar_length = len(repo_names)

    with click.progressbar(repo_names, length=progressbar_length, label='Counting commits:') as repos:
        for repo_name in repos:
            repo_dir = os.path.join(subdirectory, repo_name)

            if os.path.isdir(repo_dir):
                command = 'git rev-list --count --all --no-merges --since={0} --until={1}'\
                    .format(commits_since, commits_until)
                r = run(command, cwd=repo_dir, stdout=Capture(), stderr=Capture())

                if r.returncode == 0:
                    if r.stdout.text:
                        commits_count += int(r.stdout.text)

    if commits_year:
        click.echo('Number of commits for {0}: {1}'.format(commits_year, commits_count))


@lru_cache()
def _get_repo_names(repositories):
    return [r.name for r in repositories]


def _echo(pipeline):
    if pipeline.stderr:
        for l in pipeline.stderr.readlines():
            click.echo(l.strip())

    if pipeline.stdout:
        for l in pipeline.stdout.readlines():
            click.echo(l.strip())


@lru_cache()
def _get_token_from_file():
    try:
        with open('githuber.token', 'r') as f:
            return f.read().strip()
    except IOError:
        return None


@click.command()
@click.option('--token', help='Token', hide_input=True, default=_get_token_from_file)
@click.option('--organization', 'org_name', default=None, help='Organization name')
@click.option('--user', 'username', default=None, help='Username')
@click.option('--commits-year', default=None, help='Year to get commits for')
# @click.option('--commits-month', default=None, help='Month to get commits for')
# @click.option('--commits-day', default=None, help='Day to get commits for')
@click.option('--count', is_flag=True, help='Show the count of repos for the organization/user')
@click.option('--update', is_flag=True, help='Get any new repos and update existing repos')
@click.option('--search', 'search_regex', default=None, help='Regex pattern to search for in the code')
def main(token, org_name, username, commits_year, count, update, search_regex):
    if not token:
        return click.echo('ERROR: Please provide a token')

    if not org_name and not username:
        return click.echo('ERROR: Please provide an organization or user')

    subdirectory = org_name or username
    repo_names = None
    repositories = None

    if update:
        github = _github_login(token)
        repositories = _get_repos(github, org_name=org_name, username=username)
        update_and_retrieve_repos(repositories, subdirectory)

    if count:
        github = _github_login(token)
        repositories = _get_repos(github, subdirectory)
        repo_names = _get_repo_names(repositories)

        click.echo('Number of repos: {0}'.format(len(repo_names)))

    commits_month = None
    commits_day = None
    if commits_year or commits_month or commits_day:
        github = _github_login(token)
        repositories = _get_repos(github, subdirectory)

        if not repo_names:
            repo_names = _get_repo_names(repositories)

        get_commit_count(subdirectory, repo_names, commits_year=commits_year, commits_month=commits_month, commits_day=commits_day)

    if search_regex:
        _echo(run('grin -i {0} {1} --emacs -s --force-color'.format(search_regex, subdirectory), stdout=Capture(), stderr=Capture()))
