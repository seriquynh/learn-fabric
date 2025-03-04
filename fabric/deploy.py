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

@task(name='npm:check', desc='Check if npm exists')
def npm_check(dep: Deployer):
    dep.exec("""
        which npm
        if [ $? -ne 0 ]; 
        then 
            echo "no"
        else
            echo "yes"
        fi
    """, hide=True)

@task(name='npm:install', desc='Install NPM packages')
def npm_install(dep: Deployer):
    print('cd {{release_dir}}')
    print('npm install')

# Hooks

after('deploy:failed', 'deploy:unlock')

# Running

app.run()
