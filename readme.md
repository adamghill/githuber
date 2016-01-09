# Summary
Githuber is a command-line tool to handle keeping a large number of GitHub organization repositories up to date on your filesystem. There are also some reporting functions to get information about all of the repositories.

# Arguments
- --help: list all of the possible arguments
- --token: GitHub Personal Access Token (https://help.github.com/articles/creating-an-access-token-for-command-line-use/)
- --organization=TEXT: Name of the organization to pull repositories for
- --user=TEXT: Username to pull repositories for
- --commits-year=TEXT: Total the number commits across all repositories for the year specified
- --repo-count: Show the number of repositories
- --get-repos: Get any new repos and update existing repos

# Install
1. virtualenv .venv
1. source .venv/bin/activate
1. pip install --editable .

# Run
1. source .venv/bin/activate (if necessary)
1. githuber --token={PERSONAL_ACCESS_TOKEN} --organization=github --get-repos

# Credits
- http://github3py.readthedocs.org/
- http://pythonhosted.org/sarge/
- http://click.pocoo.org/
