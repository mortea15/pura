import os
import random
from jira import JIRA, JIRAError

JIRA_SERVER = os.getenv('JIRA_SERVER', None)
JIRA_AUTH_COOKIE = os.getenv('JIRA_AUTH_COOKIE', None)
JIRA_AUTH_BASIC = os.getenv('JIRA_AUTH_COOKIE', None)
if not JIRA_SERVER:
    #logger.error('Missing environment variable `JIRA_SERVER`.')
    pass
if JIRA_AUTH_COOKIE:
    jc = JIRA(server = JIRA_SERVER, auth = ('username', 'password'))
elif JIRA_AUTH_BASIC:
    jc = JIRA(server = JIRA_SERVER, basic_auth = ('username', 'password'))
else:
    #logger.error('Missing environment variable for authentication (`JIRA_AUTH_COOKIE` | `JIRA_AUTH_BASIC`).')
    pass


JIRA_ASSIGNEES = os.getenv('JIRA_ASSIGNEES', '').split(',')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'SEC')


def create_issue(summary, description, issue_type):
    issue = {
        'project': {'key': JIRA_PROJECT_KEY},
        'summary': summary,
        'description': description,
        'issuetype': {'name': issue_type},
    }
    return jc.create_issue(fields = issue)


def add_attachment(issue, filepath, filename=None):
    with open(filepath, 'r') as f:
        attachment = f
    return jc.add_attachment(issue, attachment, filename)


def add_comment(issue, body):
    return jc.add_comment(issue, body)


def comment_notified_user(issue, notified_username, message):
    body = f'Response sent to user {notified_username}.\n{message}'
    return add_comment(issue, body)


def assign_user(issue, username=None):
    if not username:
        username = random.choice(JIRA_ASSIGNEES)
    return jc.assign_issue(issue, username)


def search_assignable_users_for_issues():
    pass