from __future__ import division
import socket,hashlib,json,os,sys,math
BASE_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
class Client():
    def interative(self,addr,port):
        '''用户交互'''
        self.client=socket.socket()
        self.client.connect((addr,port))
        while True:
            name=input('your name>>')
            passwd=input('password>>')
            if len(name)==0 or len(passwd)==0:
                continue
            psw_md5=hashlib.md5(passwd.encode()).hexdigest()#hashlib md5加密要先对数据encode()
            account={
                'name':name,
                'passwd':passwd,
                'md5':psw_md5
            }
            self.client.send(json.dumps(account).encode())
            renzheng=self.client.recv(1024)
            if renzheng.decode()=='True':
                print('认证成功！')
                if os.path.exists(BASE_DIR+'/home/'+account['name'])==False:
                    os.mkdir(BASE_DIR+'/home/'+account['name'])#创建用户家目录
                while True:
                    cmd=input('>>')#下达指令
                    if len(cmd)==0:
                        continue
                    cmd_str=cmd.split()[0]#获取指令
                    if hasattr(self,'%s'%cmd_str):
                        func=getattr(self,'%s'%cmd_str)
                        func(cmd)
                    else:
                        self.help()
            else:
                print('认证失败！')

    def help(self):
        message='''
        有效命令:
        dir
        cd
        put filename
        get filename
        '''
        print(message)

    def put(self,*args):
        '''上传文件到用户家目录'''
        m=hashlib.md5()
        cmd=args[0].split()
        if len(cmd)>1:
            filename=cmd[1]
            if os.path.isfile(filename):
                file_size=os.stat(filename).st_size
                cmd_dic={
                    'action':'put',
                    'filename':filename,
                    'file_size':file_size
                }
                self.client.send(json.dumps(cmd_dic).encode())
                response=self.client.recv(1024)#客户端返回的指令
                if response.decode()=='True':
                    with open(filename,'rb')as f:
                        for line in f:
                            self.client.send(line)
                            size=f.tell()#用f.tell()来确定上传到哪个位置，即已上传的大小
                            self.process(size,file_size)
                            m.update(line)  # 进行md5加密
                    self.client.send(m.hexdigest().encode())  # 发送md5值给服务器
                else:
                    print(response.decode())
            else:
                print('文件不存在!')


    def get(self,*args):
        '''下载文件到dowload文件夹'''
        cmd=args[0].split()
        if len(cmd)>1:
            filename = cmd[1]
            cmd_dic={
                'action':'get',
                'filename':filename
            }
        self.client.send(json.dumps(cmd_dic).encode())
        receive=self.client.recv(1024)
        if receive.decode()=='True':
            file_size=int(self.client.recv(1024).decode())
            self.client.send(b'ready')  # 向服务端发送确认接收到数据的消息
            recv_size = 0
            recv_data = b''
            m = hashlib.md5()
            if os.path.exists(BASE_DIR + '/download/%s' % filename):
                f = open(BASE_DIR + '/download/%s' % filename + '.new', 'wb')
            else:
                f = open(BASE_DIR + '/download/%s' % filename, 'wb')
            while recv_size < file_size:  # 数据大小比较
                if file_size - recv_size > 1024:
                    size = 1024
                else:
                    size = file_size - recv_size
                data= self.client.recv(size)  # 一次接收数据
                recv_data += data
                recv_size += len(data)  # 接收到的数据大小
                m.update(data)  # MD5加密
                f.write(data)
                self.process(recv_size,file_size)
            else:
                total_md5 = self.client.recv(1024)
                # print('sever file size>>', total_size.decode(), '\n', 'recv file size', recv_size)
                print('file_md5>>', total_md5.decode())
                print('receive_md5>>', m.hexdigest())  # md5校验
        else:
            print(receive.decode())



    def dir(self,*args):
        '''查看当前目录下的文件'''
        cmd_split = args[0].split()
        if len(cmd_split) == 1 and cmd_split[0] == "dir":
            cmd_dic={
                'action':'dir',
            }
            self.client.send(json.dumps(cmd_dic).encode())
            size=self.client.recv(1024)
            self.client.send(b'ok')
            recv_size = 0
            recv_data = b''
            while recv_size < int(size.decode()):  # 数据大小比较
                data = self.client.recv(1024)  # 一次接收数据的大小
                recv_data += data
                recv_size += len(data)  # 接收到的数据
                # print(recv_size)
            else:
                print(recv_data.decode())


    def cd(self,*args):
        '''切换目录'''
        cmd_split = args[0].split()
        dirname=cmd_split[1]
        if len(cmd_split) >1 and cmd_split[0] =='cd':
            cmd_dic = {
                'action': 'cd',
                'dirname':dirname
            }
            self.client.send(json.dumps(cmd_dic).encode())
            dir_name=self.client.recv(1024)
            print(dir_name.decode())




    def process(self,size,file_size):
        '''显示进度条'''
        # percent='{:.2%}'.format(size/file_size)
        bar_length = 100  # 进度条长度,由空格和'=='组成
        percent = size/file_size
        hashes = '=' * int(percent * bar_length)  # 进度条显示的数量长度百分比
        spaces = ' ' * (bar_length - len(hashes))  # 定义空格的数量=总长度-显示长度
        sys.stdout.write(
            "\r[%s]%d%% " % ( hashes + spaces,percent*100))#percent*100:乘100后可以表示为百分数，%%：将%转义
        sys.stdout.flush()
        if size==file_size:
            # sys.stdout.write('\n上传成功！')
            sys.stdout.write('\n')


client=Client()
client.interative('localhost',2221)


