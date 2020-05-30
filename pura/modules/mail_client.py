import os
import smtplib
from imaplib import IMAP4_SSL
import email
import emailyzer

from pura.helpers.config import mail_config as CONFIG
from pura.helpers.logger import rootLogger as logger

TEMP_DIR = os.getenv('TEMP_EMAIL_DIR', '/tmp/pura')
if not os.path.exists(TEMP_DIR):
    try:
        os.mkdir(TEMP_DIR)
    except Exception as e:
        logger.error(e)


class FetchMail:
    def __init__(self):
        self.__mailbox = CONFIG.get('default_mailbox')
        self.client = IMAP4_SSL(CONFIG.get('imap').get('server'))
        self.client.login(CONFIG.get('auth').get('user'), CONFIG.get('auth').get('pass'))
        self.client.select(self.__mailbox)

    def fetch(self, _id):
        try:
            _type, data = self.client.fetch(_id, '(RFC822)')
            for res_part in data:
                if isinstance(res_part, tuple):
                    eml = res_part[1].decode('utf-8')
                    if eml:
                        return eml
        except Exception as e:
            logger.error(f'[MAILER] An error occurred while fetching the email with id `{_id}`.')
            logger.error(e)

    def read(self, eml):
        print(eml['subject'])
        print(eml['from'])

    def read_latest(self):
        try:
            ids = self.search()
            eml = self.fetch(ids[len(ids) - 1])
            self.read(eml)
        except Exception as e:
            logger.error(f'[MAILER] An error occurred while reading the latest email.')
            logger.error(e)

    def list_mailboxes(self, directory=None, pattern=None):
        try:
            mailboxes = []
            if directory and pattern:
                mailboxes = self.client.list(directory, pattern)
            elif directory:
                mailboxes = self.client.list(directory)
            else:
                mailboxes = self.client.list()
            if mailboxes:
                mailboxes = mailboxes[1]
                mailboxes = [mb.decode('utf-8') for mb in mailboxes]
                mailboxes = [mb.split('/')[1] for mb in mailboxes]
                mailboxes = [mb.replace('"', '').strip() for mb in mailboxes]
                return mailboxes
        except Exception as e:
            logger.error(f'[MAILER] An error occurred while retrieving the mailboxes.')
            logger.error(e)

    def set_mailbox(self, name):
        try:
            self.client.select(name)
            self.__mailbox = name
        except Exception as e:
            logger.error(f'[MAILER] An error occurred while setting the mailboxes to {name}.')
            logger.error(e)

    def search(self, _from=None, subject=None, criterion='ALL'):
        try:
            if _from:
                criterion = f'(FROM "{_from}")'
            if subject:
                if criterion in ['ALL', '', None]:
                    criterion = f'(SUBJECT "{subject}")'
                else:
                    criterion += f' SUBJECT "{subject}"'
            # Search for emails
            _type, data = self.client.search(None, criterion)
            ids = data[0].split()
            logger.debug(f'[MAILER] Found {len(ids)} emails in the mailbox {self.__mailbox}.')
            return ids
        except Exception as e:
            logger.error(f'[MAILER] An error occurred while searching the mailbox.')
            logger.error(e)

    def save_tmp(self, _id, eml_string):
        try:
            tempfile_path = f'{TEMP_DIR}/eml_{_id.decode("utf-8")}'
            with open(tempfile_path, 'w') as f:
                f.write(eml_string)
            return tempfile_path
        except Exception as e:
            logger.error(f'[MAILER] An error occurred while saving the EML to disk.')
            logger.error(e)
