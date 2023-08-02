#!/usr/bin/env python
"""
A handler for Sensu Go for sending alerts to Microsoft Teams in a more adapt way than
the official one, as well as other customizations.

Configuration:
  Environment variables (e.g. in a check config):
    webhook_url    Microsoft Teams webhook URL
    ICON_URL            A URL to an icon image to use for the microsoft teams user
    SENSU_BASE_URL      The base URL to the Sensu dashboard to link to. E.g. https://sensu.foo.org/ only for costum messages

  Sensu Entity labels or annotations:
    microsoft_teams_link_command_url: Toggles linking to a URL found in the check output.
    microsoft_teams_link_command_text: The link title when using microsoft_teams_link_command_url.

  microsoft teams channels can be configured using a label or annotation.
  In order of precedence:
    teams_channel annotation on entity
    teams-channel annotation on entity
    teams_channel label on entity
    teams-channel label on entity

Authors:
  * Mona Arami - https://mona-arami.github.io/ 

"""
import logging
import os
import re
import sys
import json

from datetime import datetime
from urllib.request import Request
import pymsteams


class MT:
    def __init__(self, url):
        self.url = url
    def messages(self,title,text,icon_url):
        myTeamsMessage = pymsteams.connectorcard(self.url)
        myTeamsMessage.title(title)
        myTeamsMessage.text(icon_url+text)
        return myTeamsMessage.send()
# from microsoft_teams_webhook.microsoft_teams_webhook import MT

now = datetime.now()

config = {
    "webhook_url": os.environ.get('TEST_WEBHOOK_URL'),
    "sensu_url": os.environ.get('SENSU_BASE_URL'),
    "icon_url": os.environ.get('ICON_URL', 'https://docs.sensu.io/images/sensu-logo-icon-dark@2x.png')
}

"""
List of emojis to map to an event status, using the Sensu/Nagios
exit code (0=OK, 1=Warning, 2=Critical, 3=Unknown)
"""
def emoji(status):
    emojis = [
        ':large_green_circle:',
        ':large_yellow_circle:',
        ':red_circle:',
        ':large_purple_circle:'
    ]
    return emojis[status]

def pretty_date(time=False, since=now, relative=True):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    Adapted from https://stackoverflow.com/questions/1551382/user-friendly-time-format-in-python/1551394#1551394

    :param time: the timestamp to parse
    :param since: The current time as a datetime object
    :param relative: Boolean toggling to return the time relative. E.g. "x ago"
    :return: returns a string indicating how long ago a specific time was
    """
    if isinstance(time, int):
        diff = since - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = since - time
    elif not time:
        diff = 0
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            the_time = str(second_diff)
            if relative:
                the_time = "just now"
            else:
                the_time += " seconds"
            return the_time
        if second_diff < 60:
            the_time = str(second_diff)
            if relative:
                the_time = "seconds ago"
            else:
                the_time += " seconds"
            return the_time
        if second_diff < 120:
            the_time = str(second_diff)
            if relative:
                the_time = "a minute ago"
            else:
                the_time += " seconds"
            return the_time
        if second_diff < 3600:
            the_time = str(second_diff // 60)
            the_time += " minute"
            if (second_diff // 60) > 1:
                the_time += "s"
            if relative:
                the_time += " ago"
            return the_time
        if second_diff < 7200:
            the_time = str(second_diff // 60)
            if relative:
                the_time += "an hour ago"
            else:
                the_time += " minute"
                if (second_diff // 6) > 1:
                    the_time += "s"
            return the_time
        if second_diff < 86400:
            the_time = str(second_diff // 3600)
            the_time += " hour"
            if (second_diff // 3600) > 1:
                the_time += "s"
            if relative:
                the_time += " ago"
            return the_time
    if day_diff == 1:
        the_time = str(second_diff // 3600)
        the_time += " hour"
        if (second_diff // 3600) > 1:
            the_time += "s"
        if relative:
            the_time = "Yesterday"
        return the_time
    if day_diff < 7:
        the_time = str(day_diff)
        if relative:
            the_time = " days ago"
        else:
            the_time += " days"
        return the_time
    if day_diff < 31:
        the_time = str(day_diff // 7)
        the_time += " week"
        if (day_diff // 7) > 1:
            the_time += "s"
        if relative:
            the_time += " ago"
        return the_time
    if day_diff < 365:
        the_time = str(day_diff // 30)
        the_time += " month"
        if (day_diff // 30) > 1:
            the_time += "s"
        if relative:
            the_time += " ago"
        return the_time
    if day_diff >= 365:
        the_time = str(day_diff // 365)
        the_time += " year"
        if (day_diff // 365) > 1:
            the_time += "s"
        if relative:
            the_time += " ago"
        return the_time

def parse_history(history):
    """
    Parse event history to determine the delta between the previous (bad) status
    and when it first began.
    This returns a list of the previous failed checks since the last OK

    :param history: The Sensu check's history from the event data
    :return: returns a list of the most recent failed checks since the last passing
    """
    history.reverse()
    bad_checks = []
    for i, x in enumerate(history):
        if i == 0 and x['status'] == 0:
            continue

        if x['status'] != 0:
            bad_checks.append(x)
        else:
            break
    return(bad_checks)

def get_channel(metadata):
    """
    Find a microsoft teams channel to use in labels, annotations, or an environment
    variable.

    :param metadata: The Sensu event metadata containing labels or annotations
    :return: returns a string with the microsoft teams channel to alert to
    """
    if 'annotations' in metadata:
        annotations = metadata['annotations']
        if 'teams_channel' in annotations:
            return annotations['teams_channel']
        elif 'teams-channel' in annotations:
            return annotations['teams-channel']

    if 'labels' in metadata:
        labels = metadata['labels']
        if 'teams_channel' in labels:
            return labels['teams_channel']
        elif 'teams-channel' in labels:
            return labels['teams-channel']
        else:
            #send alerts to main outages channel
            return os.environ.get('alerts-outages')

def alert_duration(history, status):
    """
    Parse the history to display how long a check has been in its status or previous status

    TODO: This is buggy and pretty limited in usefulness, since the Sensu alert
    history is limited.

    :param history: The Sensu check's history from the event data
    :param status: The Sensu check status (as int) from event metadata
    :return: returns a string with how long a check has alerted
    """
    #for i, hist in enumerate(history):
    #    if i == 0:
    #        if int(hist['status']) == 0:
    #            continue
    #    bad_history = parse_history(history)
    #    if len(bad_history) > 1:
    #        bad_first = datetime.fromtimestamp(bad_history[-1]['executed'])
    #        bad_last = datetime.fromtimestamp(bad_history[0]['executed'])
    #        #duration = str(pretty_date(bad_first, bad_last, False))
    #        #if status is 0:
    #        #    return "Alerted for " + duration
    #        #else:
    #        #    return "Alerting for " + duration
    ## Disabled for now
    return ""

def main():
    """
    Load the Sensu event data (stdin)
    """
    data = ""
    for line in sys.stdin.readlines():
        data += "".join(line.strip())
    obj = json.loads(data)
    print(obj)

    channel = get_channel(obj['entity']['metadata'])
    namespace = obj['entity']['metadata']['namespace']
    entity_name = obj['entity']['metadata']['name']
    check_name = obj['check']['metadata']['name']

    output = obj['check']['output']
    output.replace('\n', ' ').replace('\r', '')

    message = emoji(obj['check']['status'])

    """
    Generate markdown for the entity name in the microsoft teams message
    This links it to the Sensu dashboard
    """
    message += " " + f"<{config['sensu_url']}/c/~/n/{namespace}/entities/{entity_name}/events|{entity_name}>"

    """
    Generate markdown for the check name in the microsoft teams message
    This links it to the Sensu dashboard
    """
    message += " - " + f"<{config['sensu_url']}/c/~/n/{namespace}/events/{entity_name}/{check_name}|{check_name}>"

    """
    If a URL is in the check command, add a link to it in the microsoft teams message.
    This is disabled by default and can be enabled per-check by setting a
    label or annotation called 'microsoft_teams_link_command_url' to 'True' (bool)
    """
    s = False
    link_text = "(view site)"
    if 'labels' in obj['check']['metadata']:
        if 'microsoft_teams_link_command_url' in obj['check']['metadata']['labels']:
            if obj['check']['metadata']['labels']['microsoft_teams_link_command_url'].lower() == "true":
                s = True
                if 'microsoft_teams_link_command_text' in obj['check']['metadata']['labels']:
                    link_text = obj['check']['metadata']['labels']['microsoft_teams_link_command_text']
    if 'annotations' in obj['check']['metadata']:
        if 'microsoft_teams_link_command_url' in obj['check']['metadata']['annotations']:
            if obj['check']['metadata']['annotations']['microsoft_teams_link_command_url'].lower() == "true":
                s = True
                if 'microsoft_teams_link_command_text' in obj['check']['metadata']['annotations']:
                    link_text = obj['check']['metadata']['annotations']['microsoft_teams_link_command_text']

    if s:
        if 'https://' in obj['check']['command'] or 'http://' in obj['check']['command']:
            # Match the first URL in the check command
            check_url = re.findall(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", obj['check']['command'], re.I)[0]
            # Creates a string like <https://foo/bar|(visit site)>
            message += " <" + check_url + "|" + link_text + ">"

    message += ": " + output.strip()

    # Disabled for now
    #if 'history' in obj['check']:
    #    message += "; " + alert_duration(obj['check']['history'], obj['check']['status'])

    logging.debug("raw event data: %s " % str(obj))

    """
    Post to Microsoft Teams
    """
    class_microsofteams = MT(url=config['webhook_url'])
    class_microsofteams.messages(
        title = "title",
        text = message,
        icon_url = config['icon_url']
    )

if __name__ == '__main__':
    main()

