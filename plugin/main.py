from subprocess import Popen, PIPE, CREATE_NO_WINDOW
from pathlib import Path

from flox import Flox
import api


SCRIPT = 'trigger.py'
PYTHON_EXE = 'pythonw.exe'


class EspansoFlow(Flox):

    def __init__(self):
        super().__init__()
        self.espanso = api.Espanso()
        self.path = self.settings.get('path')
        if self.path == "" or self.path is None:
            self.path = api.DEFAULT_PATH
            self.settings['path'] = str(self.path)

    def query(self, query):
        if not Path(self.path).exists():
            self.add_item(
                title="Espanso not found!",
                subtitle="Please make sure your are using the latest version and set path the in settings.",
            )
            return
        snippets = self.espanso.get_snippets()
        for snippet in snippets:
            self.add_item(
                title=snippet.trigger,
                subtitle=snippet,
                method=self.activate,
                parameters=[str(snippet.match_file), snippet.trigger]
            )

    def context_menu(self, data):
        pass

    def activate(self, match_file, trigger):
        snippet = self.espanso.get_snippet(match_file, trigger)
        python_path = Path(self.python_dir).joinpath(PYTHON_EXE)
        if not python_path.exists():
            self.logger.error(f'Python executable not found: {python_path}')
        script_path = Path(self.plugindir).joinpath('plugin', SCRIPT)
        cmd = [python_path, script_path, self.path, snippet.trigger]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, creationflags=CREATE_NO_WINDOW)
        self.close_app()
        

if __name__ == "__main__":
    EspansoFlow()