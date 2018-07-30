import socketserver,hashlib,json,os,sys
BASE_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME_DIR=BASE_DIR+r'\home'
# from settings import a
class MyTcpServer(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            try:
                while True:
                    data = self.request.recv(1024)  # 接收用户名，密码
                    account=json.loads(data.decode())
                    # data['md5']=m.hexdigest()#获取MD5值
                    print(account)
                    self.PATH = BASE_DIR + r'\home\%s' % account['name']
                    renzheng=str(self.auth(account))
                    self.request.send(renzheng.encode())
                    if renzheng=='True':
                        while True:
                            cmd=self.request.recv(1024)#接收指令
                            com_dic=json.loads(cmd.decode())
                            action=com_dic['action']
                            if hasattr(self,action):
                                func=getattr(self,action)
                                func(com_dic,account)
            except ConnectionResetError as e:  # 捕获客户端断开的异常
                print(e)
                break

    def auth(self,account):
        '''用户加密认证'''
        message=''
        # print(account)
        file_exist=os.path.isfile(BASE_DIR+'/settings/%s.json'%account['name'])#判断用户文件是否存在
        # print(file_exist)
        if file_exist==True:
            DIR=BASE_DIR+'/settings/%s.json'%account['name']
            with open(DIR)as f:
                data=json.loads(f.read())
                # m.update(data['passwd'].encode())
                user_md5=hashlib.md5(data['passwd'].encode()).hexdigest()#文件中的md5
                # print(account['md5'])
                # print(user_md5)
                if account['md5']!=user_md5:#判断md5是否相同
                    # message='密码错误！'
                    return False
                else:
                    # message='认证成功！'
                    return True
        # else:
        #     message='用户不存在！'
        #     return messag

    def put(self,*args):
        '''文件上传'''
        cmd_dic=args[0]
        account=args[1]
        username=account['name']
        filename=cmd_dic['filename']
        file_size=cmd_dic['file_size']
        recv_size=0
        DIR=BASE_DIR+'/home/%s'%username
        path = BASE_DIR + '/home/%s' % account['name']
        response = self.get_dir_size(account, path)  # 空间是否足够上传文件
        self.request.send(response.encode())
        if response=='True':
            if os.path.exists(DIR+'/%s'%filename):
                f=open(DIR+'/%s'%filename+'.new','wb')
            else:
                f=open(DIR+'/%s'%filename,'wb')
            while recv_size<file_size:
                if file_size-recv_size>1024:
                    size=1024
                else:
                    size=file_size-recv_size
                data=self.request.recv(size)
                f.write(data)
                recv_size+=len(data)
            else:
                print('file has uploaded...')
                f.close()
                md5=self.request.recv(1024)
                print(md5.decode())
        # else:
        #     self.request.send(response.encode())



    def get(self,*args):
        '''文件下载'''
        cmd_dic = args[0]
        filename=cmd_dic['filename']
        if os.path.isfile(filename):
            self.request.send('True'.encode())
            m = hashlib.md5()
            file_size = os.stat(filename).st_size
            self.request.send(str(file_size).encode())  # 发送文件大小
            self.request.recv(1024)#接收客户端响应
            with open(filename, 'rb')as f:
                for line in f:
                    self.request.send(line)
                    m.update(line)  # 进行md5加密
            self.request.send(m.hexdigest().encode())  # 发送md5值给客户端
        else:
            self.request.send('文件不存在！'.encode())


    def dir(self,*args):
        '''查看当目录下文件'''
        message=os.popen('dir %s'%self.PATH).read()
        self.request.send(str(len(message.encode())).encode('utf-8'))
        self.request.recv(1024)
        self.request.send(message.encode('utf-8'))


    def cd(self,*args):
        '''切换目录'''
        account=args[1]
        com_dic=args[0]
        dir_name=com_dic['dirname']
        if dir_name=='..':
            PATH= os.path.dirname(self.PATH)
            if len(PATH)>len(self.PATH):
                self.PATH=PATH
            else:
                self.PATH=HOME_DIR+r'\%s'%account['name']
                dirname = os.path.dirname(self.PATH)
                self.request.send(dirname.encode())
        else:
        # elif dir_name!='..' and os.path.isdir(dir_name):
            PATH=self.PATH+r'\%s'%dir_name
            print(PATH)
            if len(PATH)>len(self.PATH):
                self.PATH=PATH
            dirname=os.path.dirname(self.PATH)
            self.request.send(dirname.encode())





    def get_dir_size(self,account,path):
        '''获取用户家目录大小，从而判断是否超过磁盘配额'''
        name=account['name']
        with open(BASE_DIR+'/settings/%s.json'%name,'rb')as f:
            data=json.loads(f.read())
        quota=int(data['quota'])
        size=0
        for root,dir,files in os.walk(path):
            size+=sum([os.path.getsize(os.path.join(root,name)) for name in files])
        if quota-size>2048:
            return 'True'
        else:
            return '空间不足!'




server = socketserver.ThreadingTCPServer(('localhost', 2221), MyTcpServer)
server.serve_forever()




