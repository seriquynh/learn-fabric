import typing
import getpass
from deployer import Deployer, HostDefinition

# Global variables

app = Deployer()

# Shortcuts

def host(name: str, user: str, deploy_dir: str) -> HostDefinition:
    return app.remote_add(HostDefinition(name, user, deploy_dir))

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
        app.task_define(name, desc, func)
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

def group(name: str, names):
    app.task_group(name, names)

## Core Tasks

@task(name='list', desc='List commands')
def list_commands(dep: Deployer):
    dep.io.line('List commands')

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

    # TODO: get from config('{{repository}}')
    repo_name = 'learn-fabric'

    dep.io.line(f'[%s] info > Deploying %s to %s (release %s)' % (dep.current_remote.name, repo_name, dep.io.stage, release_name))

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

group('deploy', [
    'deploy:start',
    'deploy:setup',
    'deploy:lock',
    'deploy:unlock',
])
