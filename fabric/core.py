from fabric import Connection
import re
import typer

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

class DeployerRemote:
    def __init__(self, hostname: str):
        self.data = {'hostname': hostname}

    def hostname(self, hostname: str):
        self.data['hostname'] = hostname
        return self

    def user(self, user: str):
        self.data['user'] = user
        return self

    def deploy_dir(self, deploy_dir: str):
        self.data['deploy_dir'] = deploy_dir

class Configuration:
    def __init__(self):
        self.remotes = []
        self.items = {}

    def add_remote(self, hostname: str):
        remote = DeployerRemote(hostname)
        self.remotes.append(remote)
        return remote

    def item_set(self, key: str, value):
        self.items[key] = value
        return self

    def item_add(self, key: str, value):
        pass
        return self


    def _get_data(self, key: str):
        return self.items[key]

class Deployer(typer.Typer):
    def run(self, command: str, **kwargs):
        pass
        # keys = extract_curly_braces(command)

        # for remote in self.remotes:
        #     remote.run(command)

        # command = replace_placeholders_loop(command, values)

# Global variables

config_bag = Configuration()

deployer = Deployer()

# Configuration

def host(hostname: str):
    return config_bag.add_remote(hostname)

def config(key, value):
    return config_bag.item_set(key, value)

def add(key: str, value: list):
    return config_bag.item_add(key, value)

# Hooks
def run(command: str, **kwargs):
    deployer.run(command, **kwargs)

def after(task: str, do: str):
    pass

## Input/Output

def writeln(message: str):
    print(message.replace('<success>', '').replace('</success>', ''))

def info(message: str):
    writeln("<success>info:</success> " + message)

## Tasks

@deployer.command(name='about', help='Display info with the current setup')
def about():
    print('Learn Fabric 1.0')

@deployer.command(name='deploy:info', help='Display info about deployment')
def deploy_info():
    for remote in config_bag.remotes:
        release_name = 1
        command = 'if [ -f '+remote.data['deploy_dir']+'/.dep/release_name ]; then cat '+remote.data['deploy_dir']+'/.dep/release_name; fi'
        conn = Connection(host=remote.data['hostname'], user=remote.data['user'])
        result = conn.run(command, hide=True)

        rn = result.stdout.strip()

        if rn != '':
            release_name = rn
        # TODO: dev is stage or environment. (dev, staging, production)
        writeln(f'[%s] [%s] Deploying %s to %s (release %s)' % (remote.data['hostname'], 'deploy:info', 'learn-fabric', 'dev', release_name))


@deployer.command(name='deploy:setup', help='Set up directories and files')
def deploy_setup():
    for remote in config_bag.remotes:
        writeln(f'[%s] [%s] Set up directories and files' % (remote.data['hostname'], 'deploy:setup'))

        command = """
            [ -d {{deploy_dir}} ] || mkdir -p {{deploy_dir}};
            cd {{deploy_dir}};
            [ -d .dep ] || mkdir .dep;
            [ -d releases ] || mkdir releases;
            [ -d shared ] || mkdir shared;
        """.replace('{{deploy_dir}}', remote.data['deploy_dir'])

        conn = Connection(host=remote.data['hostname'], user=remote.data['user'])
        conn.run(command)
