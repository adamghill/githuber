from github3 import login
from sarge import run, Capture
import click
import os

import logging
logger = logging.getLogger(__name__)


def _github_login(token):
    click.echo('Authenticating with token...')
    github = login(token=token)
    return github


def _get_repos(github, org_name=None, user_name=None):
    repositories = None

    if org_name:
        click.echo('Get the {0} organization...'.format(org_name))
        organization = github.organization(org_name)

        click.echo('Get repositories for {0}...'.format(org_name))
        repositories = organization.repositories()
    elif user_name:
        click.echo('Get repositories for {0}...'.format(user_name))
        raise Exception('Not implemented')
        user = github.user(user_name)
        repositories = user.subscriptions(user)
    else:
        raise Exception('No repos')

    return repositories


def clone_or_pull_repos(repositories):
    repo_count = len(_get_repo_names(repositories))
    idx = 0
    errors = []

    with click.progressbar(repositories, length=repo_count, label='Updating code:') as repos:
        for repo in repos:
            if os.path.isdir(repo.name):
                r = run('git pull origin master'.format(repo.name), cwd=repo.name, stdout=Capture(), stderr=Capture())

                if r.returncode:
                    errors.append(r.stderr.text)
            else:
                git_url = repo.git_url.replace('git://github.com/', 'git@github.com:')
                r = run('git clone {0}'.format(git_url), stdout=Capture(), stderr=Capture())

                if r.returncode:
                    errors.append(r.stderr.text)

            idx += 1

    for error in errors:
        click.echo('Error: {0}'.format(error))


def check_for_extra_repos(repo_names):
    directory_names = [d for d in os.listdir('.') if os.path.isdir(os.path.join('.', d)) and not d.startswith('.')]

    for directory_name in directory_names:
        if directory_name not in repo_names:
            click.echo('Directory is not in the list of repos: {0}'.format(directory_name))


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


def _get_repo_names(repositories):
    return [r.name for r in repositories]


@click.command()
@click.option('--token', help='Token', prompt=True, hide_input=True)
@click.option('--organization', 'org_name', default=None, help='Organization name')
@click.option('--user', 'user_name', default=None, help='Username')
@click.option('--commits-year', default=None, help='Year to get commits for')
# @click.option('--commits-month', default=None, help='Month to get commits for')
# @click.option('--commits-day', default=None, help='Day to get commits for')
@click.option('--repo-count', is_flag=True, help='Show the count of repos for the organization/user')
@click.option('--pull-repos', is_flag=True, help='Pull the repos')
def main(token, org_name, user_name, commits_year, repo_count, pull_repos):
    if not token:
        raise Exception('Please provide a token')

    if not org_name and not user_name:
        raise Exception('Please provide an organization or user')

    github = _github_login(token)
    repositories = _get_repos(github, org_name, user_name)
    repo_names = _get_repo_names(repositories)

    if repo_count:
        click.echo('Number of repos: {0}'.format(len(repo_names)))

    if pull_repos:
        clone_or_pull_repos(repositories)
        check_for_extra_repos(repo_names)

    commits_month = None
    commits_day = None
    if commits_year or commits_month or commits_day:
        get_commit_count(repo_names, commits_year=commits_year, commits_month=commits_month, commits_day=commits_day)


if __name__ == '__main__':
    main()
