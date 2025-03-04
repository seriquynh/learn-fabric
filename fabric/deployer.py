import typing
from typing_extensions import Annotated
import re
import typer

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

class DeployerIO:
    def __init__(self, selector: str = 'all', branch: str = 'main'):
        self.selector = selector
        self.branch = branch

class DeployerRemote:
    def __init__(self, alias: str):
        self.data = {'alias': alias}

    def user(self, user: str):
        self.data['user'] = user
        return self

    def deploy_dir(self, deploy_dir: str):
        self.data['deploy_dir'] = deploy_dir

class DeployerTask:
    def __init__(self, name: str, desc: str, func: typing.Callable):
        self.name = name
        self.desc = desc
        self.func = func

class Deployer:
    def __init__(self):
        self.typer_app = typer.Typer()

        self.io = DeployerIO()

        self.remotes = []
        self.items = {}
        self.tasks = []

    def remote_add(self, alias: str):
        remote = DeployerRemote(alias)
        self.remotes.append(remote)
        return remote

    def item_set(self, key: str, value):
        self.items[key] = value
        return self

    def item_add(self, key: str, value):
        pass # TODO: Append more values of a list
        return self

    def task_add(self, name: str, desc: str, func: typing.Callable):
        task_instance = DeployerTask(name, desc, func)

        self.tasks.append(task_instance)

        @self.typer_app.command(name=name, help=desc)
        def command_func(selector: str = typer.Argument(default='all'), branch: Annotated[str, typer.Option(help="The git repository branch.")] = "main",):
            self.io.selector = selector
            self.io.branch = branch
            func(self)
        return self

    def run(self):
        self.typer_app()


# Global variables

app = Deployer()

# Configuration

def host(alias: str):
    return app.remote_add(alias)

def config(key, value):
    return app.item_set(key, value)

def add(key: str, value: list):
    return app.item_add(key, value)

## Input/Output

def writeln(message: str):
    print(message.replace('<success>', '').replace('</success>', ''))

def info(message: str):
    writeln("<success>info:</success> " + message)

# Hooks

def after(job: str, do: str):
    pass

## Core
def run(command: str, **kwargs):
    pass

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

@task(name='about', desc='Display info with the current setup')
def about():
    print('Learn Fabric 1.0')

@task(name='deploy:info', desc='Display info about deployment')
def deploy_info(dep: Deployer):
    for remote in dep.remotes:
        if dep.io.selector == 'all' or dep.io.selector == remote.data['alias']:
            release_name = 1
            command = 'if [ -f '+remote.data['deploy_dir']+'/.dep/release_name ]; then cat '+remote.data['deploy_dir']+'/.dep/release_name; fi'
            conn = Connection(host=remote.data['alias'], user=remote.data['user'])
            result = conn.run(command, hide=True)

            rn = result.stdout.strip()

            if rn != '':
                release_name = rn
            # TODO: dev is stage or environment. (dev, staging, production)
            writeln(f'[%s] [%s] Deploying %s to %s (release %s)' % (remote.data['alias'], 'deploy:info', 'learn-fabric', 'dev', release_name))

@task(name='deploy:setup', desc='Set up directories and files')
def deploy_setup(dep: Deployer):
    for remote in dep.remotes:
        writeln(f'[%s] [%s] Set up directories and files' % (remote.data['alias'], 'deploy:setup'))

        command = """
            [ -d {{deploy_dir}} ] || mkdir -p {{deploy_dir}};
            cd {{deploy_dir}};
            [ -d .dep ] || mkdir .dep;
            [ -d releases ] || mkdir releases;
            [ -d shared ] || mkdir shared;
        """.replace('{{deploy_dir}}', remote.data['deploy_dir'])

        conn = Connection(host=remote.data['alias'], user=remote.data['user'])
        conn.run(command)
