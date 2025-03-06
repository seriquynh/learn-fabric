import typing

from typing_extensions import Annotated
import re
import typer

from fabric import Connection

class InputOutput:
    VERBOSITY_QUIET = 'quiet'
    VERBOSITY_NORMAL = 'normal'
    VERBOSITY_VERBOSE = 'verbose'
    VERBOSITY_DEBUG = 'debug'

    def __init__(self, selector: str = 'all', branch: str = 'main', stage: str = 'dev'):
        self.selector = selector
        self.branch = branch
        self.stage = stage
        self.verbosity = self.VERBOSITY_NORMAL

    def line(self, line: str = ''):
        if self.verbosity == InputOutput.VERBOSITY_QUIET:
            return
        
        print(line.replace('<success>', '').replace('</success>', ''))

class HostDefinition:
    def __init__(self, name: str, user: str, deploy_dir: str):
        self.name = name
        self.user = user
        self.deploy_dir = deploy_dir

class TaskDefinition:
    def __init__(self, name: str, desc: str, func: typing.Callable):
        self.name = name
        self.desc = desc
        self.func = func

class Deployer:
    def __init__(self):
        self.console = typer.Typer()

        self.io = None
        self.current_remote = None

        self.config = {}
        self.remotes = []
        self.tasks = []

    def remote_add(self, remote: HostDefinition) -> HostDefinition:
        self.remotes.append(remote)
        return remote

    def config_set(self, key: str, value):
        self.config[key] = value
        return self

    def config_add(self, key: str, value):
        pass # TODO: Append more values of a list
        return self

    def task_define(self, name: str, desc: str, func: typing.Callable):
        task = TaskDefinition(name, desc, func)

        @self.console.command(name=name, help=desc)
        def task_func(selector: str = typer.Argument(default='all'),
                         branch: Annotated[str, typer.Option(help="The git repository branch.")] = "main",
                         stage: Annotated[str, typer.Option(help="The deploy stage.")] = "dev",
                         quiet: Annotated[bool, typer.Option(help="Do not print any output.")] = None,
                         verbose: Annotated[bool, typer.Option(help="Print debug output.")] = None,):
            if self.io is None:
                self.io = InputOutput()
                self.io.selector = selector
                self.io.branch = branch
                self.io.stage = stage

                if quiet:
                    self.io.verbosity = InputOutput.VERBOSITY_QUIET
                elif verbose:
                    self.io.verbosity = InputOutput.VERBOSITY_DEBUG
                else:
                    self.io.verbosity = InputOutput.VERBOSITY_NORMAL

            for remote in self.remotes:
                if selector == 'all' or remote.name == selector:
                    self.current_remote = remote
                    self.io.line(f'[%s] task > %s' % (remote.name, name))
                    try:
                        func(self)
                    except:
                        pass

        self.tasks.append(task)

        return self

    def task_group(self, name: str, task_names):
        desc = f'Task group "%s" [%s]' % (name, ', '.join(task_names))

        @self.console.command(name=name, help=desc)
        def task_group_func(selector: str = typer.Argument(default='all'),
                      branch: Annotated[str, typer.Option(help="The git repository branch.")] = "main",
                      stage: Annotated[str, typer.Option(help="The deploy stage.")] = "dev",
                      quiet: Annotated[bool, typer.Option(help="Do not print any output.")] = False,
                      verbose: Annotated[bool, typer.Option(help="Print debug output.")] = False,):
            if self.io is None:
                self.io = InputOutput()
                self.io.selector = selector
                self.io.branch = branch
                self.io.stage = stage

                if quiet:
                    self.io.verbosity = InputOutput.VERBOSITY_QUIET
                elif verbose:
                    self.io.verbosity = InputOutput.VERBOSITY_DEBUG
                else:
                    self.io.verbosity = InputOutput.VERBOSITY_NORMAL

            for remote in self.remotes:
                if self.io.selector == 'all' or remote.name == self.io.selector:
                    self.current_remote = remote
                    self.io.line(f'[%s] task > %s' % (remote.name, name))
                    for task_name in task_names:
                        for t in self.tasks:
                            if t.name == task_name:
                                self.io.line(f'[%s] task > %s' % (remote.name, task_name))
                                try:
                                    t.func(self)
                                except:
                                    pass

        return self

    def run(self, command: str, **kwargs):
        remote = self.current_remote

        if remote is None:
            return

        command = self.parse(command, {
            'stage': self.io.stage,
        })

        if self.io.verbosity == InputOutput.VERBOSITY_DEBUG:
            self.io.line(f'[%s] run > %s' % (remote.name, command))

        conn = Connection(host=remote.name, user=remote.user)

        res = conn.run(command, **kwargs)

        return res

    def parse(self, text: str, params: dict = None) -> str:
        remote = self.current_remote
        if remote is not None:
            text = text.replace('{{deploy_dir}}', remote.deploy_dir)

        keys = self._extract_curly_braces(text)

        for key in keys:
            if params is not None and key in params:
                text = text.replace('{{' + key + '}}', params[key])
            elif key in self.config:
                text = text.replace('{{' + key + '}}', self.config[key])

        return text

    @staticmethod
    def _extract_curly_braces(text):
        pattern = r'\{\{([^}]*)\}\}'
        matches = re.findall(pattern, text)
        return matches
