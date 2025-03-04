from core import deployer, host, config, add, after

# Config

config('repository', 'git@github.com:seriquynh/learn-fabric.git')

add('shared_files', [])
add('shared_dirs', [])
add('writable_dirs', [])

# Hosts

host('ubuntu-1').user('vagrant').deploy_dir('~/learn-fabric/dev')
host('ubuntu-2').user('vagrant').deploy_dir('~/learn-fabric/dev')

# Hooks

after('deploy:failed', 'deploy:unlock')

deployer()
