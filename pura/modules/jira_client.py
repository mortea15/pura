import os
import sys
import random
from jira import JIRA, JIRAError

from pura.helpers.logger import rootLogger as logger

JIRA_SERVER = os.getenv('JIRA_SERVER', None)
JIRA_USER = os.getenv('JIRA_USER', None)
JIRA_TOKEN = os.getenv('JIRA_TOKEN', None)
if not JIRA_SERVER:
    logger.error('[JIRA  ] Missing environment variable `JIRA_SERVER`.')
    sys.exit(2)
if not JIRA_USER and JIRA_TOKEN:
    logger.error('[JIRA  ] Missing environment variables for authentication (`JIRA_USER` and `JIRA_PASS`).')
    sys.exit(2)

jc = JIRA(JIRA_SERVER, basic_auth = (JIRA_USER, JIRA_TOKEN))


JIRA_ASSIGNEES = os.getenv('JIRA_ASSIGNEES', '').split(',')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'SEC')

MIN_CONFIDENCE_LEVEL = os.getenv('MIN_CONFIDENCE_LEVEL', 85)


templates = {
    'summary': '[%classification%] for user %recipient%',
    'description': 'User %recipient% received a %classification% email on %timedate%.\nSender: %email_sender%\nSubject: %email_subject%\n\nConfidence level: %confidence_level%\nActions taken: See comments'
}

PRIORITIES = {
    '1': 'Highest',
    '2': 'High',
    '3': 'Medium',
    '4': 'Low',
    '5': 'Lowest'
}


def __create_issue(summary, description, issue_type='Task'):
    try:
        logger.debug(f'[JIRA  ] Creating new issue for project `{JIRA_PROJECT_KEY}`.')
        issue = {
            'project': {'key': JIRA_PROJECT_KEY},
            'summary': summary,
            'description': description,
            'issuetype': {'name': issue_type},
        }
        return jc.create_issue(fields = issue)
    except JIRAError as jc_err:
        logger.error(jc_err)
    except Exception as err:
        logger.error(err)

def __add_attachment(issue_key, filepath, filename='email'):
    try:
        logger.debug(f'[JIRA  ] Adding attachment to issue `{issue_key}`.')
        return jc.add_attachment(issue_key, filepath, filename)
    except JIRAError as jc_err:
        logger.error(jc_err)
        __add_comment(issue_key, f'Uploading of email attachment `{filename}` failed.')
    except FileNotFoundError:
        logger.error(f'[JIRA  ] File `{filepath}` does not exist.')
    except Exception as err:
        logger.error(f'[JIRA  ] An error occurred while uploading an attachment to issue `{issue_key}`.')
        logger.error(err)
        __add_comment(issue_key, f'Uploading of email attachment `{filename}` failed.')


def __add_comment(issue_key, body):
    try:
        logger.debug(f'[JIRA  ] Adding comment to issue `{issue_key}`.')
        return jc.add_comment(issue_key, body)
    except JIRAError as jc_err:
        logger.error(jc_err)
    except Exception as err:
        logger.error(err)


def __assign_user(issue_key, accountId=None):
    assigned = False
    try:
        logger.debug(f'[JIRA  ] Assigning user for issue `{issue_key}`..')
        if not accountId:
            logger.debug(f'[JIRA  ] No accountId provided. Selecting random user.')
            users = __search_assignable_users_for_projects()
            if users:
                logger.debug(f'[JIRA  ] User search: {len(users)} users found.')
                accountId = random.choice(users).accountId
            else:
                logger.error(f'[JIRA  ] No assignable users were found for this project.')
                return assigned
            assigned = jc.assign_issue(issue_key, accountId)
            logger.debug(f'[JIRA  ] User assigned: {assigned}')
    except JIRAError as jc_err:
        logger.error(jc_err)
    except Exception as err:
        logger.error(err)

    return assigned

def __search_assignable_users_for_projects():
    try:
        logger.debug(f'[JIRA  ] Searching for assignable users for project `{JIRA_PROJECT_KEY}`.')
        assignable = jc.search_assignable_users_for_projects('', JIRA_PROJECT_KEY)
    except JIRAError as jc_err:
        logger.error(jc_err)
    except Exception as err:
        logger.error(err)


def __set_priority(issue, priority_key):
    try:
        logger.debug(f'[JIRA  ] Setting priority for issue `{issue.key}`.')
        issue.update(
            fields = {
                'priority': {
                    'id': priority_key,
                    'name': PRIORITIES.get(priority_key)
                }
            }
        )
        logger.debug(f'[JIRA  ] Priority for issue `{issue.key}` set to `{PRIORITIES.get(priority_key)}` ({priority_key}).')
    except JIRAError as jc_err:
        logger.error(jc_err)
    except Exception as err:
        logger.error(err)


def __determine_priority(issue, classification):
    logger.debug(f'[JIRA  ] Determining priority for issue `{issue.key}`.')
    pri = '2'
    classification = classification.lower()
    if classification == 'malware':
        pri = '1'
    elif classification == 'phishing':
        pri = '2'
    elif classification == 'fraud':
        pri = '2'
    elif classification == 'spam':
        pri = '3'
    elif classification == 'legitimate':
        pri = '5'

    __set_priority(issue, pri)    


def __parse_template(classification, confidence_level, recipient, email_sender, email_subject, timedate):
    keys = {
        '%classification%': classification,
        '%recipient%': recipient,
        '%timedate%': timedate,
        '%email_sender%': email_sender,
        '%email_subject%': email_subject,
        '%confidence_level%': confidence_level
    }

    summary = templates.get('summary')
    desc = templates.get('description')

    for k, v in keys.items():
        summary = summary.replace(k, v)
        desc = desc.replace(k, v)

    return summary, desc


def create_issue(classification, confidence_level, recipient, email_sender, email_subject, timedate, attachment_filepath=None, comment=''):
    try:
        summary, desc = __parse_template(classification, confidence_level, recipient, email_sender, email_subject, timedate)
        issue = __create_issue(summary, desc)
        if issue:
            __determine_priority(issue, classification)

            if int(float(confidence_level)) < MIN_CONFIDENCE_LEVEL:
                logger.debug(f'[JIRA  ] Assigning user to handle manually due to low confidence level [level: {confidence_level}]')
                assigned = __assign_user(issue.key)
                logger.debug(f'[JIRA  ] Setting priority to `Highest` due to low confidence level [level: {confidence_level}]')
                __set_priority(issue, '1')
            if attachment_filepath:
                __add_attachment(issue.key, attachment_filepath, 'email')
            if comment:
                __add_comment(issue.key, comment)
        else:
            logger.error(f'[JIRA  ] An error occurred while creating the issue in JIRA.')
    except JIRAError as jc_err:
        logger.error(jc_err)
    except Exception as err:
        logger.error(err)


def add_comment_user_notified(issue_key, notified_user, message='', via='email'):
    try:
        body = f'Response sent to user {notified_user} via {via}.'
        if message:
            body += f'\nMessage:\n  {message}'
        return __add_comment(issue_key, body)
    except JIRAError as jc_err:
        logger.error(jc_err)
    except Exception as err:
        logger.error(err)


def main():
    if jc:
        classification = 'Phishing'
        confidence_level = '86.9'
        recipient = 'u.ser@mail.ru'
        email_sender = 'e.vil@corp.ir'
        email_subject = 'Please verify your contact details'
        timedate = '15/04/2020:13:37'
        attach = None
        create_issue(classification, confidence_level, recipient, email_sender, email_subject, timedate, attachment_filepath=attach, comment='')


if __name__ == '__main__':
    main()