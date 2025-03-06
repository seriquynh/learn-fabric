from deployer import Deployer, app, host, config, add, task, after


# Hosts
host(name='ubuntu-1', user='vagrant', deploy_dir='~/learn-fabric/{{stage}}')
host(name='ubuntu-2', user='vagrant', deploy_dir='~/learn-fabric/{{stage}}')

# Config

config('repository', 'https://github.com/laravel/laravel.git')

add('shared_files', [])
add('shared_dirs', [])
add('writable_dirs', [])


# Tasks

@task(name='npm:install', desc='Install NPM packages')
def npm_install(dep: Deployer):
    dep.run('cd {{deploy_dir}} && npm install')

# Hooks

after('deploy:failed', 'deploy:unlock')

# Running

app.console()
