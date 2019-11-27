import paramiko

# 创建SSH对象
ssh = paramiko.SSHClient()
# 允许连接不在know_hosts文件中的主机
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# 连接服务器
ssh.connect(hostname='192.168.122.77', port=22,
            username='root', password='123')
# 执行命令  stdout命令结果，stderr错误
stdin, stdout, stderr = ssh.exec_command('df -hl')
# 获取命令结果
result = stdout.read()
print(result)
# 关闭连接
ssh.close()
