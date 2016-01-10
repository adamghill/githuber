from functools32 import lru_cache
from github3 import login
from sarge import run, Capture
import click
import os


import logging
logger = logging.getLogger(__name__)


@lru_cache()
def _github_login(token):
    click.echo('Authenticating with token...')
    github = login(token=token)
    return github


@lru_cache()
def _get_repos(github, org_name=None, username=None):
    repositories = None

    if org_name:
        click.echo('Get the {0} organization...'.format(org_name))
        organization = github.organization(org_name)

        click.echo('Get repositories for the "{0}"" organization...'.format(org_name))
        repositories = organization.repositories()
    elif username:
        click.echo('Get repositories for the "{0}" user...'.format(username))
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
                    errors.append(r.stderr.text)

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
                    errors.append(r.stderr.text)

    return errors


def update_and_retrieve_repos(repositories, subdirectory):
    repo_names = _get_repo_names(repositories)
    directory_names = _get_directory_names(subdirectory)

    errors = []
    errors.extend(_update_existing_repos(subdirectory, repo_names, directory_names))
    errors.extend(_retrieve_new_repos(subdirectory, repositories, repo_names, directory_names))

    for error in errors:
        click.echo('ERROR: {0}'.format(error))

    for directory_name in directory_names:
        if directory_name not in repo_names:
            click.echo('Directory is not in the list of repos: {0}'.format(directory_name))


def _get_directory_names(subdirectory):
    if not os.path.isdir(subdirectory):
        os.mkdir(subdirectory)

    directory_names = [d for d in os.listdir(subdirectory) if os.path.isdir(os.path.join(subdirectory, d)) and not d.startswith('.')]
    return directory_names


def get_commit_count(repo_names, commits_year=None, commits_month=None, commits_day=None):
    click.echo('Get commit count...')
    commits_count = 0
    commits_since = None
    commits_until = None

    if commits_year:
        commits_since = '01/01/{0}'.format(commits_year)
        commits_until = '12/31/{0}'.format(commits_year)
    elif commits_month:
        raise Exception('Not implemented')
    elif commits_day:
        raise Exception('Not implemented')
    else:
        raise Exception('Not implemented')

    for repo_name in repo_names:
        if os.path.isdir(repo_name):
            command = 'git rev-list --count --all --no-merges --since={0} --until={1}'\
                .format(commits_since, commits_until)
            r = run(command,
                cwd=repo_name, stdout=Capture(), stderr=Capture())

            if r.returncode > 0:
                commits_count += int(r.stdout.text)

    click.echo('Number of commits: {0}'.format(commits_count))


@lru_cache()
def _get_repo_names(repositories):
    return [r.name for r in repositories]


@click.command()
@click.option('--token', help='Token', prompt=True, hide_input=True)
@click.option('--organization', 'org_name', default=None, help='Organization name')
@click.option('--user', 'username', default=None, help='Username')
@click.option('--commits-year', default=None, help='Year to get commits for')
# @click.option('--commits-month', default=None, help='Month to get commits for')
# @click.option('--commits-day', default=None, help='Day to get commits for')
@click.option('--repo-count', is_flag=True, help='Show the count of repos for the organization/user')
@click.option('--get-repos', is_flag=True, help='Get any new repos and update existing repos')
@click.option('--search', 'search_regex', default=None, help='Regex pattern to search for in the code')
def main(token, org_name, username, commits_year, repo_count, get_repos, search_regex):
    if not token:
        return click.echo('ERROR: Please provide a token')

    if not org_name and not username:
        return click.echo('ERROR: Please provide an organization or user')

    subdirectory = org_name or username

    if get_repos:
        github = _github_login(token)
        repositories = _get_repos(github, org_name=org_name, username=username)
        update_and_retrieve_repos(repositories, subdirectory)

    if repo_count:
        github = _github_login(token)
        repositories = _get_repos(github, subdirectory)
        repo_names = _get_repo_names(repositories)

        click.echo('Number of repos: {0}'.format(len(repo_names)))

    commits_month = None
    commits_day = None
    if commits_year or commits_month or commits_day:
        get_commit_count(repo_names, commits_year=commits_year, commits_month=commits_month, commits_day=commits_day)

    if search_regex:
        r = run('grin -i {0} {1} --emacs -s --force-color'.format(search_regex, subdirectory), stdout=Capture(), stderr=Capture())

        if r.stderr.text:
            click.echo(r.stderr.text)

        if r.stdout.text:
            click.echo(r.stdout.text)
