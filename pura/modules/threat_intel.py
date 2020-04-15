import os
import re
import sys
from urllib.parse import urlparse

import requests
from requests.exceptions import HTTPError

import pura.helpers.regex as REGEX
from pura.helpers.logger import rootLogger as logger

# TODO Cache files in temp dir
CACHE_FILES = bool(int(os.getenv('CACHE_THREAT_FEEDS', '1')))

FEEDS = {
    'plain': [
        'https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt',    # IPsum suspicious/malicious hosts
        'https://cinsscore.com/list/ci-badguys.txt',    # Collective Intelligence Network Security
        'https://openphish.com/feed.txt',   # OpenPhish
        'https://panwdbl.appspot.com/lists/mdl.txt' # Malware Domain List,
        'https://cybercrime-tracker.net/all.php'    # Cybercrime known hosts
    ],
    'csv': [
        'https://data.phishtank.com/data/online-valid.csv', # PhishTank
    ]
}


def __get_fqdn(host):
    try:
        o = urlparse(host)
        if o.netloc:
            return o.netloc
        else:
            logger.warning('[TH-INT] No netloc found in host.')
    except ValueError as e:
        logger.error(f'[TH-INT] An error occurred while parsing a host.')
        logger.error(e)

    return host


def __get_fqdn_path(host):
    try:
        o = urlparse(host)
        if o.netloc:
            if not o.path:
                logger.warning('[TH-INT] No path found in host.')
            return f'{o.netloc}{o.path}'
        else:
            logger.warning('[TH-INT] No netloc found in host.')
    except ValueError as e:
        logger.error(f'[TH-INT] An error occurred while parsing a host.')
        logger.error(e)

    return host


def __is_ip(host):
    try:
        match = re.match(REGEX.IP, host, re.IGNORECASE)
    except Exception as e:
        logger.error(e)
    if match:
        return True

    return False


def __is_url(host):
    try:
        match = re.match(REGEX.URL, host, re.IGNORECASE)
    except Exception as e:
        logger.error(e)
    if match:
        return True

    return False


def __fetch_feed(feed):
    with requests.Session() as session:
        try:
            res = session.get(feed)
            res.raise_for_status()
        except HTTPError as http_err:
            logger.error(f'[TH-INT] HTTP error while fetching a feed\n{http_err}')
        except Exception as err:
            logger.error(f'[TH-INT] An error occurred while fetching a feed\n{err}')
    if res and res.text:
        try:
            return res.text.split('\n')
        except Exception:
            return res.text

    return None


def __parse_csv(response):
    hosts = []
    if response:
        try:
            if isinstance(response, list):
                headers = response.pop(0).split(',')
                try:
                    index = headers.index('url')
                except ValueError:
                    try:
                        index = headers.index('ip')
                    except ValueError:
                        logger.error(f'[TH-INT] Unable to find either [url, ip] in headers of CSV. Returning empty list.')
                        return hosts

                for line in response:
                    line = line.split(',')
                    try:
                        data = line[index]
                        if data:
                            if __is_ip(data) or __is_url(data):
                                hosts.append(data)
                    except IndexError:
                        pass
            else:
                logger.error('[TH-INT] Response is not of expected type `list`. Returning empty list.')
        except Exception as e:
            logger.error(e)
    else:
        logger.error('[TH-INT] Response is empty. No CSV to parse.')

    return hosts


def __strip_feed(feed):
    parsed = []
    # Remove comments, blank lines, and any counts
    feed = [line.split()[0] for line in feed if not line.startswith('#') and line != '']
    # Some FEEDS use dashes (-) for IP ranges
    # Split them up and add each to the main list
    # TODO: Get the full range, not just split
    for line in feed:
        match = re.match(REGEX.IP_MULTI, line, re.IGNORECASE)
        if match:
            print(line)
            ips = line.split('-')
            parsed += ips
        else:
            parsed.append(line)
    return parsed


def __is_in_feed(host, feed):
    feed = __strip_feed(feed)
    if __is_ip(host):
        if host in feed:
            logger.debug(f'[TH-INT] Host {host} found in feed (src: IP, exact)')
            return True, 1.0
    if __is_url(host):
        fqdn_path = __get_fqdn_path(host)
        if fqdn_path in feed:
            logger.debug(f'[TH-INT] Host {host} found in feed (src: FQDN/path, exact)')
            return True, 1.0
        fqdn = __get_fqdn(host)
        if fqdn in feed:
            logger.debug(f'[TH-INT] Host {host} found in feed (src: FQDN, exact)')
            return True, 1.0
    if host in feed:
        logger.debug(f'[TH-INT] Host {host} found in feed (src: full, exact)')
        return True, 1.0

    # No direct match, look deeper.
    # Look for partial matches
    match = [line for line in feed if host in line]
    if __is_url(host):
        fqdn_path = __get_fqdn_path(host)
        match = [line for line in feed if fqdn_path in line]
        if match:
            logger.debug(f'[TH-INT] Host {host} found in feed (src: FQDN/path, partial) [match: {match}]')
            return True, 0.9
        fqdn = __get_fqdn(host)
        match = [line for line in feed if fqdn in line]
        if match:
            logger.debug(f'[TH-INT] Host {host} found in feed (src: FQDN, partial) [match: {match}]')
            return True, 0.6
    if __is_ip(host):
        match = [line for line in feed if host in line]
        if match:
            logger.debug(f'[TH-INT] Host {host} found in feed (src: IP, partial) [match: {match}]')
            return True, 0.6
    if match:
        logger.debug(f'[TH-INT] Host {host} found in feed (src: full, partial) [match: {match}]')
        return True, 0.7

    return False, 0.0


def is_threat(hosts):
    """Check whether a host is present in selected threat intelligence sources

        Parameters
        ----------
        hosts : list
            A list of IP addresses, FQDNs and/or URLs to look for.

        Returns
        -------
        results : list
            A list of objects in the following format:
                { 'host': string, 'found': bool, 'confidence': float, 'feed_url': string }
                host : string
                    The hostname (IP, FQDN or URL)
                found : bool
                    Whether the host was found.
                confidence : float
                    A confidence level from 0.0 to 1.0.
                feed_url : string
                    The URL of the threat intel where the host was found.
    """
    results = []

    logger.info(f'[TH-INT] Checking host {len(hosts)} against threat intel feeds.')
    
    for feed_url in FEEDS['plain']:
        if len(results) == len(hosts):
            return results
        feed = __fetch_feed(feed_url)
        if feed:
            for host in hosts:
                found = False
                host = host.strip()
                found, confidence = __is_in_feed(host, feed)
                if found:
                    results.append({ 'host': host, 'found': found, 'confidence': confidence, 'feed_url': feed_url })
                    break
        else:
            logger.error(f'[TH-INT] Feed for {feed_url} is None or empty. Skipping.')
    for feed_url in FEEDS['csv']:
        if len(results) == len(hosts):
            return results
        feed = __fetch_feed(feed_url)
        if feed:
            feed = __parse_csv(feed)
            if feed:
                for host in hosts:
                    found = False
                    host = host.strip()
                    found, confidence = __is_in_feed(host, feed)
                    if found:
                        results.append({ 'host': host, 'found': found, 'confidence': confidence, 'feed_url': feed_url })
                        break
            else:
                logger.error(f'[TH-INT] No feed was returned from parsing the CSV.')
        else:
            logger.error(f'[TH-INT] Feed for {feed_url} is None or empty. Skipping.')
    return results


def main():
    if len(sys.argv) > 1:
        hosts = sys.argv[1]
        hosts = hosts.split(',')
        results = is_threat(hosts)
        if results:
            for result in results:
                logger.debug(f'[TH-INT] From feed: {result["feed_url"]}')
                print(f'Host: {result["host"]}')
                print(f'Threat: {"true" if result["found"] else "false"}')
                print(f'Confidence: {result["confidence"]}')
                print()
    else:
        logger.error(f'[TH-INT] Missing argument for `host`')
        print('Please specify a host to look for as the first argument.')


if __name__ == '__main__':
    main()