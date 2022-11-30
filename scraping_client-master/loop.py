import threading
from os import system
from datetime import datetime

class ThreadJob(threading.Thread):
    def __init__(self,callback,event,interval):
        
        self.callback = callback
        self.event = event
        self.interval = interval
        super(ThreadJob,self).__init__()

    def run(self):
        while not self.event.wait(self.interval):
            self.callback()

event = threading.Event()

def foo():
    f = open("when.txt", "r")
    when = f.readline()    
    now = datetime. now()
    dt_string = now. strftime("%A %H:%M:%S")
    print(dt_string)
    if(dt_string == when) :
        print ("OK! Upload and Downloading XLS File now")
        system("up_down_load_xls.exe")

k = ThreadJob(foo,event,1)
k.start()

print ("It is non-blocking")