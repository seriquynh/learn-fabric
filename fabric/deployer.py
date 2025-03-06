import typing

from typing_extensions import Annotated
import re
import typer
import getpass

from fabric import Connection

def extract_curly_braces(text):
    pattern = r'\{\{([^}]*)\}\}'
    matches = re.findall(pattern, text)
    return matches

def replace_placeholders_loop(template, values_dict):
    # First extract all placeholders
    placeholders = re.findall(r'\{\{([^}]*)\}\}', template)

    # Make a copy of the template
    result = template

    # Replace each placeholder
    for placeholder in placeholders:
        if placeholder in values_dict:
            result = result.replace(f"{{{{{placeholder}}}}}", values_dict[placeholder])

    return result

class InputOutput:
    def __init__(self, selector: str = 'all', branch: str = 'main', stage: str = 'dev'):
        self.selector = selector
        self.branch = branch
        self.stage = stage

class RemoteHost:
    def __init__(self, name: str, user: str, deploy_dir: str):
        self.name = name
        self.user = user
        self.deploy_dir = deploy_dir

class DeployerTask:
    def __init__(self, name: str, desc: str, func: typing.Callable):
        self.name = name
        self.desc = desc
        self.func = func

class Deployer:
    def __init__(self):
        self.current_remote = None

        self.console = typer.Typer()
        self.io = InputOutput()

        self.config = {}
        self.remotes = []
        self.tasks = []

    def remote_add(self, remote: RemoteHost) -> RemoteHost:
        self.remotes.append(remote)
        return remote

    def config_set(self, key: str, value):
        self.config[key] = value
        return self

    def config_add(self, key: str, value):
        pass # TODO: Append more values of a list
        return self

    def task_add(self, name: str, desc: str, func: typing.Callable):
        task_instance = DeployerTask(name, desc, func)

        self.tasks.append(task_instance)

        @self.console.command(name=name, help=desc)
        def command_func(selector: str = typer.Argument(default='all'),
                         branch: Annotated[str, typer.Option(help="The git repository branch.")] = "main",
                         stage: Annotated[str, typer.Option(help="The deploy stage.")] = "dev",):
            self.io.selector = selector
            self.io.branch = branch
            self.io.stage = stage

            for remote in self.remotes:
                if selector == 'all' or remote.name == selector:
                    self.current_remote = remote
                    self.line(f'[%s] task %s' % (remote.name, name))
                    func(self)

        return self

    def task_group(self, name: str, task_names):
        def func(dep: Deployer):
            for remote in dep.remotes:
                if dep.io.selector == 'all' or remote.name == dep.io.selector:
                    dep.current_remote = remote
                    for task_name in task_names:
                        for t in dep.tasks:
                            if t.name == task_name:
                                dep.line(f'[%s] task %s' % (remote.name, task_name))
                                t.func(dep)
                                break

        desc = f'Task group "deploy" [%s]' % ', '.join(task_names)

        return self.task_add(name, desc, func)

    @staticmethod
    def line(line: str = ''):
        print(line.replace('<success>', '').replace('</success>', ''))

    def run(self, command: str, **kwargs):
        remote = self.current_remote

        if remote is None:
            return

        command = self.parse(command, {
            'stage': self.io.stage,
        })

        self.line(f'[%s] run %s' % (remote.name, command))

        conn = Connection(host=remote.name, user=remote.user)

        res = conn.run(command, **kwargs)

        return res

    def parse(self, text: str, params: dict = None) -> str:
        remote = self.current_remote
        if remote is not None:
            text = text.replace('{{deploy_dir}}', remote.deploy_dir)

        keys = extract_curly_braces(text)

        for key in keys:
            if params is not None and key in params:
                text = text.replace('{{' + key + '}}', params[key])
            elif key in self.config:
                text = text.replace('{{' + key + '}}', self.config[key])

        return text


# Global variables

app = Deployer()

# Configuration

def host(name: str, user: str, deploy_dir: str) -> RemoteHost:
    return app.remote_add(RemoteHost(name, user, deploy_dir))

def config(key, value):
    return app.config_set(key, value)

def add(key: str, value: list):
    return app.config_add(key, value)

# Hooks

def after(job: str, do: str):
    pass

def before(job: str, do: str):
    pass

# Others

def task(name: str, desc: str):
    def caller(func: typing.Callable):
        app.task_add(name, desc, func)
        def wrapper(*args, **kwargs):
            # Do something before the function call
            print("Before the function call")

            # Call the original function
            result = func(*args, **kwargs)

            # Do something after the function call
            print("After the function call")
            return result
        return wrapper
    return caller

## Core Tasks

@task(name='list', desc='List commands')
def list_commands(dep: Deployer):
    dep.line('List commands')

@task(name='deploy:start', desc='Start a new deployment')
def deploy_start(dep: Deployer):
    command = """
        if [ -f {{deploy_dir}}/.dep/release_name ]; then
            cat {{deploy_dir}}/.dep/release_name
        elif [ -f {{deploy_dir}}/.dep/latest_release ]; then
            LATEST_RELEASE_NAME="$(cat {{deploy_dir}}/.dep/latest_release)"
            RELEASE_NAME=$((LATEST_RELEASE_NAME + 1))
            echo $RELEASE_NAME
        else
            echo 1 > {{deploy_dir}}/.dep/release_name
            echo 1
        fi
    """

    res = dep.run(command, hide=True)

    release_name = res.stdout.strip()

    dep.line(f'[%s] info Deploying %s to %s (release %s)' % (dep.current_remote.name, 'learn-fabric', 'dev', release_name))

@task(name='deploy:lock', desc='Lock the deploy task')
def deploy_lock(dep: Deployer):
    user = getpass.getuser()
    res = dep.run("[ -f {{deploy_dir}}/.dep/deploy.lock ] && echo +locked || echo "+user+" > {{deploy_dir}}/.dep/deploy.lock")
    locked = res.stdout.strip()
    if locked == '+locked':
        locked_user = dep.run("cat {{deploy_dir}}/.dep/deploy.lock")
        raise Exception(f"Deploy locked by %s. Execute 'deploy:unlock' task to unlock." % locked_user)

@task(name='deploy:unlock', desc='Unlock the deploy task')
def deploy_unlock(dep: Deployer):
    dep.run('rm -rf {{deploy_dir}}/.dep/deploy.lock')

@task(name='deploy:setup', desc='Set up directories and files')
def deploy_setup(dep: Deployer):
    command = """
        [ -d {{deploy_dir}} ] || mkdir -p {{deploy_dir}};
        cd {{deploy_dir}};
        [ -d .dep ] || mkdir .dep;
        [ -d releases ] || mkdir releases;
        [ -d shared ] || mkdir shared;
    """
    dep.run(command)

app.task_group('deploy', [
    'deploy:start',
    'deploy:setup',
    'deploy:lock',
])
