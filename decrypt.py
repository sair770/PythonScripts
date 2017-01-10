import os
from sys import argv
from string import maketrans


file_name = argv[1]

def rot13(text):
    text = "".join(map(lambda x:chr(ord(x)-13),text)) 
    return text
try: 
    def encrypt():
        global file_name
        file_open = open(file_name,'rb')
        file_write = open(file_name.strip('.enc'),'wb')
        for line in file_open:
            line = line.strip('\n')
            line = line.strip('\r')
            line = line[::-1]   
            line = rot13(line)
            print line
            file_write.write(line)
        file_write.close()
        file_open.close()
        print "Successfully Encrypted the file"
        cmd = "rm "+file_name
        os.system(cmd)
except Exception,e:
    print "Fucking Error :" + e
    
if __name__ == '__main__':
    encrypt()
