from fabric.api import env, sudo, task


@task(default=True)
def default():
	env.user = 'root'
	env.password = '123'
	env.sudo_password = env.password
	env.hosts = ['192.168.122.77']
	env.port = 22
	sudo("df -h /dev/nvme0n1")
