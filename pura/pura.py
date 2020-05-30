#!/usr/bin/env python
# -*- coding: utf-8 -*-
import emailyzer
import juicer
import katatasso
import os

from pura.modules.threat_intel import is_threat
from pura.modules.jira_client import create_issue, add_comment_user_notified
from pura.modules.mail_client import FetchMail
from pura.helpers.logger import rootLogger as logger
from katatasso.helpers.const import categories

TRAININGDATA_PATH = os.getenv('TRAININGDATA_PATH', '../trainingdata/train/spam')
ALGO = os.getenv('algo', 'mnb')


def fetch_emails(limit=10):
    emls = []
    i = 0
    try:
        client = FetchMail()
        #client.set_mailbox('Junk')
        res = client.search()
        while i <= limit:
            for _id in res:
                eml_str = client.fetch(_id)
                tempfile_path = client.save_tmp(_id, eml_str)
                emls.append(emailyzer.from_eml(tempfile_path))
                i += 1
        return emls
    except Exception as e:
        logger.error(f'[PURA  ] An error occurred while fetching the email.')
        logger.error(e)
    return emls


def classify(eml):
    try:
        if eml:
            content = eml.html_as_text
            hosts = eml.hosts
            # Preprocess, extract entities
            words = juicer.extract_stanford(content, named_only=False, stemming=False)
            category = katatasso.classifyv2(words, algo=ALGO)

            return {
                'label': category,
                'class': categories[category],
                'recipient': 'hidden',
                'sender': eml.sender,
                'subject': eml.subject,
                'timedate': eml.date,
                'hosts': hosts,
                'file': eml.filepath
            }
    except Exception as e:
        logger.error(f'[PURA  ] An error occurred while classifying the email.')
        logger.error(e)
    return None


def report_event(classification, confidence, recipient, sender, subject, timedate, attachment_filepath=None):
    try:
        create_issue(classification, confidence, recipient, sender, subject, timedate, attachment_filepath=attachment_filepath, comment='')
    except:
        logger.critical(f'Failed to create JIRA issue for {classification} event (from={sender},subject={subject}.')


def handle_event(eml):
    response = classify(eml)
    if response:
        print(f'{response.get("class")} ({response.get("label")})')
        if response.get('hosts'):
            threat = is_threat(response.get('hosts'))
            print(threat)

        report_event(response.get('class'), '0.0', response.get('recipient'), response.get('sender'), response.get('subject'), response.get('timedate'), attachment_filepath=response.get('file'))