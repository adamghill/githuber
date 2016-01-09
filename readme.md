# Summary
Githuber is a command-line tool to handle keeping a large number of GitHub organization repositories up to date on your filesystem. There are also some reporting functions to get information about all of the repositories.

# Arguments
- --help: list all of the possible arguments
- --token: GitHub Personal Access Token ()
- --organization=TEXT: Name of the organization to pull repositories for
- --commits-year=TEXT: Total the number commits across all repositories for the year specified
- --repo-count: Show the number of repositories
- --get-repos: Get any new repos and update existing repos

# Install
1. virtualenv .venv
1. source .venv/bin/activate
1. pip install -r requirements.txt

# Run
1. source .venv/bin/activate (if necessary)
1. python pull.py --token={PERSONAL_ACCESS_TOKEN} --organization=github --get-repos
