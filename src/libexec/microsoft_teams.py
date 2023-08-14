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
import requests


now = datetime.now()
print("-----------")
print(sys.path[0])
print("-----------")
def get_env_variables():
    
    config = {
        #webhook url will assign in each entity metadata
        "outages_webhook_url": os.environ.get('OUTAGES_TEAMS_WEBHOOK_URL'),
        "sensu_url": os.environ.get('SENSU_BASE_URL'),
        "icon_url": os.environ.get('ICON_URL', 'https://docs.sensu.io/images/sensu-logo-icon-dark@2x.png')
    }
    return config

"""
List of emojis to map to an event status, using the Sensu/Nagios
exit code (0=OK, 1=Warning, 2=Critical, 3=Unknown)
"""
def get_state(status):
    #status is int number , critical (2), 	 warning (1), 	 success (0), 	 unknown (3)
    if status == 1:
        state = "Warning"
    elif status == 2:
        state = "Critical"
    elif status == 3:
        state = "Unknown"
    else:
        state = "Success"
    return state

def convert_time():
    return "'"

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


def get_event_data():
    """
    Load the Sensu event data (stdin)
    """
    data = ""
    for line in sys.stdin.readlines():
        data += "".join(line.strip())
    event_data = json.loads(data)
    print(event_data.keys())
    return event_data   

def get_sensu_url (data,b_url):
    #https://sensu.snafu.cr.usgs.gov/c/~/n/dev/events/atb-conservation-beta/check-http
    namespace = data['entity']['metadata']['namespace']
    entity_name = data['entity']['metadata']['name']
    check_name = data['check']['metadata']['name']
    """
    Generate markdown for the entity name in the microsoft teams message
    This links it to the Sensu dashboard
    """
    # sensu_url = f"{b_url}/c/~/n/{namespace}/entities/{entity_name}/events|{entity_name}"

    """
    Generate markdown for the check name in the microsoft teams message
    This links it to the Sensu dashboard
    """
    sensu_url = ""
    # sensu_url = f"<{b_url}/c/~/n/{namespace}/events/{entity_name}/{check_name}>"
    sensu_url += f"{b_url}/c/~/n/{namespace}/events/{entity_name}/{check_name}"
    """
    handel value for "microsoft_teams_link_command_text" , 'microsoft_teams_link_command_url' to 'True' (bool)
    """
    s = False
    link_text = "(view site)"
    if 'labels' in data['check']['metadata']:
        if 'microsoft_teams_link_command_url' in data['check']['metadata']['labels']:
            if data['check']['metadata']['labels']['microsoft_teams_link_command_url'].lower() == "true":
                s = True
                if 'microsoft_teams_link_command_text' in data['check']['metadata']['labels']:
                    link_text = data['check']['metadata']['labels']['microsoft_teams_link_command_text']
   
    if 'annotations' in data['check']['metadata']:
        if 'microsoft_teams_link_command_url' in data['check']['metadata']['annotations']:
            if data['check']['metadata']['annotations']['microsoft_teams_link_command_url'].lower() == "true":
                s = True
                if 'microsoft_teams_link_command_text' in data['check']['metadata']['annotations']:
                    link_text = data['check']['metadata']['annotations']['microsoft_teams_link_command_text']

    
    if s:
        if 'https://' in data['check']['command'] or 'http://' in data['check']['command']:
            # Match the first URL in the check command
            check_url = re.findall(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", data['check']['command'], re.I)[0]
            # Creates a string like <https://foo/bar|(visit site)>
            sensu_url += " <" + check_url + "|" + link_text + ">"

    
    return sensu_url


    

def main():
    #start test
    # with open('sample-event2.json') as f:
    #     test_data = json.load(f)
    # obj = test_data['spec']
    # web_url = "https://xxx.webhook.office.com/"
    # base_url = "https:xxxxx"
    # sensu_url = get_sensu_url(obj,base_url)
    # args = [obj['entity']['metadata']['namespace'],
    #         obj['entity']['metadata']['name'],
    #         obj['entity']['entity_class'],
    #         obj['check']['metadata']['name'],
    #         obj['check']['state'],
    #         obj['entity']['metadata']['labels']['proxy_type'],
    #         obj['entity']['metadata']['labels']['url'],
    #         obj['check']['output'].replace('\n', ' ').replace('\r', ''),
    #         sensu_url
    #         ]

    # card_load = {
    # "text":'''{8}

    #     Sensu Event
    #     -------------------------------
    #     NameSpace     {0}
    #     Entity        {1}
    #     Class         {2}
    #     Check         {3}
    #     State         {4}
    #     Proxy Type    {5}
    #     URL           {6}
    #     Output        {7}
    # '''.format(*args)
    # }

    # d = json.dumps(card_load)
    # print("ddddddddd", d)
    # headers = {"Content-Type": "application/json"}
    
    # print("-----------------")
    # response = requests.post(web_url, json=card_load, headers=headers)
    # requests.post(web_url, data=json.dumps(card_load),headers=headers)

    # print("-----------------")
    # print("SAS Microsoft Teams Channels response status: ", response)
    # print("-----------------")
    #finish test


    #start 
    event_data = get_event_data()
    env_var_dic = get_env_variables()
    sensu_url = get_sensu_url(event_data,env_var_dic['sensu_url'])
    args = [event_data['entity']['metadata']['namespace'],
            event_data['entity']['metadata']['name'],
            event_data['entity']['entity_class'],
            event_data['check']['metadata']['name'],
            event_data['check']['state'],
            event_data['entity']['metadata']['labels']['proxy_type'],
            event_data['entity']['metadata']['labels']['url'],
            event_data['check']['output'].replace('\n', ' ').replace('\r', ''),
            sensu_url
            ]
    card_load = {
    "text":'''{8}

        Sensu Event
        -------------------------------
        NameSpace     {0}
        Entity        {1}
        Class         {2}
        Check         {3}
        State         {4}
        Proxy Type    {5}
        URL           {6}
        Output        {7}
    '''.format(*args)
    }
    logging.debug("raw event data: %s " % str(event_data))
    # jsonData = {
    #     "text": output_alert
    # }
    headers = {"Content-Type": "application/json"}
    # #send alert message to alerts-outages MSteams channel
    response_outages = requests.post(env_var_dic['outages_webhook_url'], json=card_load, headers=headers)
    # #send alert message to apps MSteams channel
    # # response_apps = requests.post(web, json={"message": output_alert})

    print("-----------------")
    print("SAS Microsoft Teams Channels response status: ", response_outages)
    print("-----------------")

if __name__ == '__main__':
    main()
