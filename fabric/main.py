from fabric import Connection

c = Connection('ubuntu')

result = c.run('whoami', hide=True)

print(result)

result = c.run('uname -a', hide=True)

print(result)
