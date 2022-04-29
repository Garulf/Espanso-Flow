import yaml
from pathlib import Path
import os
import logging
from datetime import datetime


log = logging.getLogger(__name__)

PROG = 'espanso.cmd'
APPLOCAL = Path(os.getenv('LOCALAPPDATA'))
ROAMING = Path(os.getenv('APPDATA'))
DEFAULT_PATH = APPLOCAL.joinpath("Programs", "Espanso", PROG)
MATCH_DIR = ROAMING.joinpath('Espanso', 'match')
TRIGGER_ARG = '-t'


class Espanso:

    def __init__(self):
        pass

    def get_matches(self):
        for match_file in Path.glob(MATCH_DIR, '*.yml'):
            yield MatchFile(match_file)

    def get_match(self, match_file):
        return MatchFile(match_file)

    def get_snippets(self):
        snippets = []
        for match in self.get_matches():
            for snippet in match.snippets():
                snippets.append(snippet)
        return snippets

    def get_snippet(self, match_file, trigger):
        match = self.get_match(match_file)
        return match.snippet(trigger)


class MatchFile:
    
    def __init__(self, match_file):
        self.match_file = match_file
    
    def read(self, file):
        snippets = []
        with open(file, 'r') as f:
            snippets.append(yaml.safe_load(f))
        return snippets

    def snippet(self, trigger):
        for snippet in self.snippets():
            if snippet.trigger == trigger:
                return snippet

    def snippets(self):
        matches = self.read(self.match_file)
        for snippet in matches[0]['matches']:
            yield Snippet(self.match_file, snippet)

class Snippet:

    def __init__(self, match_file, data):
        self.match_file = match_file
        self.data = data
        for item in data:
            setattr(self, item, data[item])

    def type(self):
        return self.data.get('vars', [{'type': None}])[0].get('type')

    def __str__(self) -> str:
        if self.type() == 'date':
            date_fmt = self.data.get('vars', [{'params': {'format': None}}])[0].get('params').get('format')
            now = datetime.now()
            return str(now.strftime(date_fmt))
        return self.replace



if __name__ == '__main__':
    e = Espanso()
    s = e.get_snippets()
    for snippet in s:
        print(snippet)