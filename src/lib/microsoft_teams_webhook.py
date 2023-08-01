from __future__ import annotations
from urllib.request import Request, urlopen
import json
import pymsteams

class MicrosoftTeams:
    def __init__(self, url):
        self.url = url
    def messages(self,title,text,icon_url):
        myTeamsMessage = pymsteams.connectorcard(self.url)
        myTeamsMessage.title(title)
        myTeamsMessage.text(icon_url+text)
        return myTeamsMessage.send()
