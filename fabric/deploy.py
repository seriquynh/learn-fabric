from deployer import Deployer, app, host, config, add, task, after

# Config

config('repository', 'https://github.com/laravel/laravel.git')

add('shared_files', [])
add('shared_dirs', [])
add('writable_dirs', [])

# Hosts

host('ubuntu-1').user('vagrant').deploy_dir('~/learn-fabric/dev')
host('ubuntu-2').user('vagrant').deploy_dir('~/learn-fabric/dev')

# Tasks

@task(name='npm:install', desc='Install NPM packages')
def npm_install(dep: Deployer):
    print('cd {{release_dir}}')
    print('npm install')

# Hooks

after('deploy:failed', 'deploy:unlock')

# Running

app.run()
