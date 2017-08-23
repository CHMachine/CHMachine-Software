import cv2
import numpy as np
from PIL import ImageGrab
from tkinter import *
import win32gui
import win32con
import pyHook # pyhook_py3k is advised
import serial
import threading
import serial.tools.list_ports
import pygame

version = '0.9.2'

serialbaud=9600
streamwindowssizex=220
streamwindowssizey=220


def keysetup(file):
    global pausebutton
    global slowdownbutton
    global speedupbutton
    global screenshotbutton
    global refreshbutton

    #default keys:
    pausebutton='Numpad0'
    slowdownbutton='Numpad1'
    speedupbutton='Numpad2'
    screenshotbutton='F9'
    refreshbutton='F10'

    try:
        setup  = open(file, 'r')

        for x in range(100):
            setuplist=setup.readline().replace(" ", "").strip().split('=')
            #print (setuplist)
            if setuplist[0] == 'Pause':
                pausebutton=setuplist[1]

            if setuplist[0] == 'Slowdown':
                slowdownbutton=setuplist[1]
    
            if setuplist[0] == 'Speedup':
                speedupbutton=setuplist[1]

            if setuplist[0] == 'Screenshot':
                screenshotbutton=setuplist[1]
        
            if setuplist[0] == 'Refresh':
                refreshbutton=setuplist[1]

            if setuplist[0]== '***':
                setup.close()          
                break
    except:
        print('Cannot open', file, ', loading default keys...\n')
        

def comportsetup():
    global ports
    ports = list(serial.tools.list_ports.comports()) # detects available ports

    #prints available ports
    print ('- AVAILABLE PORTS:\n') 
    for p in ports:
        print (p) 
    print('')
   

        
        

class motorclass():
    def __init__(self):
        self.state=2
        self.tempo=0
        self.savestate=2
        self.tempokeepalive=0
        self.tempokeepalive_A=0
        self.tempokeepalive_B=0
        self.keepalivems=100
        self.result=0 
        self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create an array of zeros for the black background
     
    def detect(self):
        

        while 1:
           
            while (self.state==5): # DETECT SETUP
                arr = np.array(ImageGrab.grab(bbox=((pos[0]-xsize),(pos[1]-ysize),(pos[0]+xsize),(pos[1]+ysize))))
                arr = cv2.cvtColor(arr,cv2.COLOR_RGB2BGR)
                self.result = cv2.matchTemplate(arr, arrbase, cv2.TM_CCOEFF_NORMED)
                try:#take care of sliding too fast which result in a shape out of boundaries
                    if self.result>0:
                        print ('%.0f %% Match' %(self.result*100))
                    else:
                        print ('0 % Match')

                    
                    if checkinv==False: #invert flag False
                       
                        if (self.result>=treshold):#turn on the pin if the match value is over the threshold
                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background
                            cv2.circle(self.colorshow,(0,0), 63, (0,255,0), -1) #draw a green circle
                            self.tempo=pygame.time.get_ticks()
                    
                        elif (pygame.time.get_ticks()-self.tempo) >= (timeonvar):  #turn off the pin some time after the last match is occurred 
                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background
                
                    else: #invert flag True
                    
                        if (self.result<=treshold):#turn on the pin if the match value is under the threshold
                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background
                            cv2.circle(self.colorshow,(0,0), 63, (0,255,0), -1) #draw a green circle
                            self.tempo=pygame.time.get_ticks()
                    
                        elif (pygame.time.get_ticks()-self.tempo) >= (timeonvar):  #turn off the pin some time after the last match is occurred 
                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background
                    #centering and overlapping images over background:
                    x_offset=int(streamwindowssizex/2 - xsize) 
                    y_offset=int(streamwindowssizey/2 - ysize) 
                    self.colorshow[y_offset:y_offset + arr.shape[0], x_offset:x_offset + arr.shape[1]] = arr   
                
                except:
                    pass
                   
                        
                cv2.imshow('Stream', self.colorshow)  #showing image
                cv2.waitKey(1)
     
           
           
           
           
           
            while (self.state==1): ################# DETECT
                
                arr = np.array(ImageGrab.grab(bbox=((pos[0]-xsize),(pos[1]-ysize),(pos[0]+xsize),(pos[1]+ysize))))
                arr=cv2.cvtColor(arr,cv2.COLOR_RGB2BGR)
                self.result = cv2.matchTemplate(arr, arrbase, cv2.TM_CCOEFF_NORMED)
                try:#take care of sliding too fast which result in a shape out of boundaries


                    if checkinv==False: ###invert flag False
                        
                        if (self.result>=treshold):#turn on the pin if the match value is over the threshold
                            if pygame.time.get_ticks()-self.tempokeepalive_A>=self.keepalivems:#send serial data every 100ms to avoid flooding
                                self.PWMpin(speed) 
                                self.tempokeepalive_A=pygame.time.get_ticks()
                                self.tempokeepalive_B=0
                                self.tempokeepalive=pygame.time.get_ticks()
                            self.tempo=pygame.time.get_ticks()
                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background
                            cv2.circle(self.colorshow,(0,0), 63, (0,255,0), -1) #draw a green circle
                                                  

                        elif (pygame.time.get_ticks()-self.tempo) >= (timeonvar): #turn off the pin some time after the last match is occurred

                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background  
                       
                            if pygame.time.get_ticks()-self.tempokeepalive_B>=self.keepalivems:#send serial data every 100ms to avoid flooding
                                self.PWMpin(floorspeed)
                                self.tempokeepalive_B=pygame.time.get_ticks()
                                self.tempokeepalive_A=0
                                self.tempokeepalive=pygame.time.get_ticks()
                         
                          
                    else:                    ###invert flag True
                        
                        if (self.result<=treshold):#turn on the pin if the match value is under the threshold
                            if pygame.time.get_ticks()-self.tempokeepalive_A>=self.keepalivems:#send serial data every 100ms to avoid flooding
                                self.PWMpin(speed) 
                                self.tempokeepalive_A=pygame.time.get_ticks()
                                self.tempokeepalive_B=0
                                self.tempokeepalive=pygame.time.get_ticks()
                            self.tempo=pygame.time.get_ticks()
                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background
                            cv2.circle(self.colorshow,(0,0), 63, (0,255,0), -1) #draw a green circle
                                                  

                        elif (pygame.time.get_ticks()-self.tempo) >= (timeonvar): #turn off the pin some time after the last match is occurred

                            if pygame.time.get_ticks()-self.tempokeepalive_B>=self.keepalivems:#send serial data every 100ms to avoid flooding
                                self.PWMpin(floorspeed)
                                self.tempokeepalive_B=pygame.time.get_ticks()
                                self.tempokeepalive_A=0
                                self.tempokeepalive=pygame.time.get_ticks()
                                

                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background                         
                            

                    #centering and overlapping image over background:
                    x_offset=int(streamwindowssizex/2 - xsize) 
                    y_offset=int(streamwindowssizey/2 - ysize) 
                    self.colorshow[y_offset:y_offset + arr.shape[0], x_offset:x_offset + arr.shape[1]] = arr  
                                
                except:
                    pass

                  
                cv2.imshow('Stream', self.colorshow)  #showing image
                cv2.waitKey(1)

                try:
                    if  pygame.time.get_ticks()-self.tempokeepalive>=self.keepalivems: #keeps the pin on(see arduino code)

                        arduino.write(('K').encode('utf-8')) 
                        self.tempokeepalive=pygame.time.get_ticks()

                except serial.SerialTimeoutException: 
                    print('WRITE TIMEOUT ERROR.')
                    arduino.close()
                    self.stop()

                except:
                    pass


            
            while self.state==2:#################### STOP/PAUSE
                
                self.PWMpin('0')
                
                pygame.time.wait(self.keepalivems)



            while self.state==3: ##################### ALWAYS ON
                        
                self.PWMpin(speed)
                pygame.time.wait(self.keepalivems)
                  
                  
                      

            while self.state==4:######################### PULSE
                
                self.tempo=pygame.time.get_ticks()
                self.PWMpin(speed)

                while (pygame.time.get_ticks()-self.tempo) < (timeonvar):
                    pygame.time.wait(1)
                    if self.state!=4:
                        break
                    if (pygame.time.get_ticks()-self.tempokeepalive) >= self.keepalivems:
                        
                        arduino.write(('K').encode('utf-8'))
                        self.tempokeepalive = pygame.time.get_ticks()

                                   
                
                self.tempo=pygame.time.get_ticks()
                self.PWMpin(floorspeed)

                while (pygame.time.get_ticks()-self.tempo) < (timeoffvar):
                    pygame.time.wait(1)
                    if self.state!=4:
                        break
                    if (pygame.time.get_ticks()-self.tempokeepalive) >= self.keepalivems:
                       
                        arduino.write(('K').encode('utf-8'))
                        self.tempokeepalive = pygame.time.get_ticks()
                

                     
           
    def PWMpin(self, PWM_speed): #set the PWM of the microcontroller pin
        try:
            arduino.write(('V' + PWM_speed + 'S').encode('utf-8'))

        except serial.SerialTimeoutException: 
            print('WRITE TIMEOUT ERROR.')
            arduino.close()
            self.stop()

        except:
            pass
       


    def stop(self):
        self.state=2
        self.savestate=2

    def pause(self):
       
        if self.state!=2:
            self.savestate=self.state
            self.state=2
            

        elif self.state==2:
            self.state=self.savestate
        

    def startdetect(self):
        self.state=1
        self.savestate=self.state

    def alwayson(self):
        self.state=3
        self.savestate=self.state

    def pulse(self):
        self.state=4
        self.savestate=self.state

    def setup(self):
        self.state=5
        self.savestate=self.state
 
def serialstartauto(COMstring, baud): 

    global arduino
    line=('')
    comentry.delete(0, 'end')  # delete text from the widget  
    root.focus() #remove focus from the entry widget
    
    
    resetGUI()
    motor.stop() 
         
    try:
        arduino.close()
        pygame.time.wait(750)
    except:
        pass
    print("Looking for the CH Machine, PLEASE WAIT...\n")
    for p in ports: 
        try:
                
            arduino = serial.Serial('COM' + (p[0][3:5]), baud, timeout = 1, write_timeout = 1) # 2=Com3 on windows always a good idea to specify a timeout incase we send bad data
            print ('COM' + p[0][3:5] + '...')
            pygame.time.wait(1000)# wait for arduino to initialize
            arduino.flushInput()
            arduino.flushOutput()
            pygame.time.wait(1000)
            arduino.write(('T').encode('utf-8'))#
            pygame.time.wait(250)

            line = arduino.read(6).decode(encoding='UTF-8',errors='strict')
            #print (line)
            
            if line.find('connOK')!=-1:#
                print("CHM CONNECTED!")
                arduino.write(('V0S').encode('utf-8'))
                print ('COM' + p[0][3:5] + '  - Initialization Complete.')
                break
            else: #
                print ('wrong connection.')
                arduino.close()
                pygame.time.wait(250)  
                   
        except:
            print ('exception')

    if line.find('connOK')==-1:
        print ('\nCH Machine NOT found, check out the connection.\n')


def serialstart(COMstring, baud):
    global arduino
    line=('')
    comentry.delete(0, 'end')  # delete text from the widget  
    root.focus() #remove focus from the entry widget
    
    
    if COMstring ==(''): #autofinding correct COM port
        serialstartauto(COMstring, baud)

    
        
    #manual COM port:
    elif COMstring.isdigit()==True:

        print ('COM' + COMstring + ' - Initializing...')
        resetGUI()
        motor.stop()   
         
        try:
            arduino.close()
            pygame.time.wait(750)
        except:
            pass

        try:
            arduino = serial.Serial(('COM' + str(COMstring)), baud, timeout = 1, write_timeout = 1) # 2=Com3 on windows always a good idea to specify a timeout incase we send bad data
            pygame.time.wait(800)
            arduino.write(('V0S').encode('utf-8'))
            print ('COM' + COMstring + ' - Initialization Complete.')
          
        except serial.SerialTimeoutException:
            print ('COM' + COMstring + ' TIMEOUT EXCEPTION. Try another port.')
            arduino.close()
                
        except:
            if COMstring.isdigit()==True:
                print('COM' + COMstring +' - No port found.')
            else:
                print('No port found.')
                
    elif (COMstring !=('') and COMstring.isdigit()==False):
        print('Digits only')

            

def onKeyDown(event):
    
    global speed
    #print ('MessageName:',event.MessageName)
    #print ('Message:',event.Message)
    #print ('Time:',event.Time)
    #print ('Window:',event.Window)
    #print ('WindowName:',event.WindowName)
    #print ('Ascii:', event.Ascii, chr(event.Ascii))
    #print ('Key:', event.Key)
    #print ('KeyID:', event.KeyID)
    #print ('ScanCode:', event.ScanCode)
    #print ('Extended:', event.Extended)
    #print ('Injected:', event.Injected)
    #print ('Alt', event.Alt)
    #print ('Transition', event.Transition)
    #print ('---')

        # never put any condition first other than event.key 
    if event.Key == ('Return'):
        
        if comentry==root.focus_get() and comentry.get()!=(''):
            serialstart(comtext.get(), serialbaud)
       
    
    if event.Key == (slowdownbutton):
        
        speedint=int(speed)
        if (checkAOVar.get()==True or checkPULVar.get()==True or checkDETVar.get()==True or checkSETVar.get()==True):
            if speedint>10:
                speedint -= 10
                motorspeed.set(speedint)
                speed=str(speedint)
                
            else:
                motorspeed.set(0)
                speed=('0')
                


    if event.Key == (speedupbutton): 
        speedint=int(speed)
        if (checkAOVar.get()==True or checkPULVar.get()==True or checkDETVar.get()==True or checkSETVar.get()==True):
            if speedint <= 245:
                speedint += 10
                motorspeed.set(speedint)
                speed=str(speedint)
                
            else:
                motorspeed.set(255)
                speed=('255')
        

    if event.Key == (pausebutton): 
        motor.pause()

    if (event.Key == screenshotbutton or event.Key == refreshbutton):
        
        global pos
        global arrbase
        if (event.Key == screenshotbutton):
            pos=win32gui.GetCursorPos() 
        
        if (pos!=None):
            print(pos)  
        
            arrbase = np.array(ImageGrab.grab(bbox=((pos[0]-xsize),(pos[1]-ysize),(pos[0]+xsize),(pos[1]+ysize))))
            arrbase=cv2.cvtColor(arrbase,cv2.COLOR_RGB2BGR)


            x_offset=int(streamwindowssizex/2 - xsize)
            y_offset=int(streamwindowssizey/2 - ysize)  
            base=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create black background
            cv2.imshow('Stream',base)
        
            base[y_offset:y_offset+arrbase.shape[0], x_offset:x_offset+arrbase.shape[1]] = arrbase
            cv2.imshow('Match_1',base)
            cv2.waitKey(1)

            hwndstream = win32gui.FindWindow(None,'Stream')
            rectstream = win32gui.GetWindowRect(hwndstream)
            win32gui.SetWindowPos(hwndstream, win32con.HWND_TOPMOST, rectstream[0], rectstream[1], rectstream[2]-rectstream[0], rectstream[3]-rectstream[1], 0) 

            hwndmatch = win32gui.FindWindow(None,'Match_1')
            rectmatch = win32gui.GetWindowRect(hwndmatch)
            win32gui.SetWindowPos(hwndmatch, win32con.HWND_TOPMOST, rectmatch[0], rectmatch[1], rectmatch[2]-rectmatch[0], rectmatch[3]-rectmatch[1], 0) 

                  
    return True


    
    
# TKINTER FUNCTIONS: 
 

    
def slidersize(value):
    global arrbase
    global xsize
    global ysize
    xsize=sizex.get()*(streamwindowssizex - 20)/200
    ysize=sizey.get()*(streamwindowssizey - 20)/200
    try:#at startup an exception occur (pos=none)
        arrbase = np.array(ImageGrab.grab(bbox=((pos[0]-xsize),(pos[1]-ysize),(pos[0]+xsize),(pos[1]+ysize))))
        arrbase=cv2.cvtColor(arrbase,cv2.COLOR_RGB2BGR)
        x_offset=int( streamwindowssizex/2 - xsize)
        y_offset=int( streamwindowssizey/2 - ysize)  
        baseshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create black background
        baseshow[y_offset:y_offset+arrbase.shape[0], x_offset:x_offset+arrbase.shape[1]] = arrbase
        cv2.imshow('Match_1', baseshow)
        cv2.waitKey(1)  
    except:
        pass 


def alwaysONtick():
    
    try:
        arduino.write(('K').encode('utf-8'))


        if checkAOVar.get()==False:
            motor.stop()

       
        if checkAOVar.get()==True:
            resetGUI()
            checkAO.select()
            motor.alwayson()

        
    except:
        print('No serial connection')
        checkAO.deselect()


def detecttick():
     

     if (pos==None):
            print('Position? (Press', screenshotbutton, 'to take a screenshot)')
            checkDET.deselect()
            

     else:
        try:
            arduino.write(('K').encode('utf-8'))

        
            if checkDETVar.get()==False:
                motor.stop()
        
            if checkDETVar.get()==True:
                resetGUI()
                checkDET.select()
                motor.startdetect()
        except:
            print('No serial connection')
            checkDET.deselect()

       
def detectsetup():
     

     if (pos==None):
            print('Position? (Press', screenshotbutton, 'to take a screenshot)')
            checkSET.deselect()

     else:
              

        if checkSETVar.get()==False:
            motor.stop()

        if checkSETVar.get()==True:
            resetGUI()
            checkSET.select()
            try:
                arduino.write(('V0S').encode('utf-8'))
            except:
                pass
            motor.setup()




def pulsetick():
    try:
        arduino.write(('K').encode('utf-8'))


        if checkPULVar.get()==False:
            motor.stop()
        
        if checkPULVar.get()==True:
            resetGUI()
            checkPUL.select()
            motor.pulse()
    except:
        print('No serial connection')
        checkPUL.deselect()


def on_closing():
    print ('Bye Bye')
    try:
        arduino.write(('V0S').encode('utf-8'))
        arduino.close()
    except:
        pass

    root.destroy()
    print ('Be vigilant')
    sys.exit()



def speedslider(value):
    global speed
    speed=value

def floorspeedslider(value):
    global floorspeed
    floorspeed=value

def timeONslider(value):
    global timeonvar
    timeonvar=int(value)
    


def timeOFFslider(value):
    global timeoffvar
    timeoffvar=int(value)

    
def tresholdslider(value):
    global treshold
    treshold=int(value)/100
   

def about():
   
    top = Toplevel()
    top.wm_attributes("-topmost", 1)
    top.resizable(0, 0)
    top.focus()
    top.geometry("200x150")
    top.title('About')
    top.iconbitmap('favicon.ico')

    msg  = Message(top, width=300, text='COCK HERO MACHINE Ver.' + version)
    msga = Message(top, width=300, text='cockheromachine@gmail.com')
    msgb = Message(top, width=300, text='For more informations visit:')
    msgc = Message(top, width=300, text='cockheromachine.blogspot.com\n')
    msg.pack()
    msga.pack()
    msgb.pack()
    msgc.pack()

    button = Button(top, height=1, width=10, text="OK", command=top.destroy)
    button.pack()


def alwaysONtop():

    root.wm_attributes("-topmost", not root.wm_attributes("-topmost"))

def resetGUI():

    checkAO.deselect()
    checkPUL.deselect()
    checkDET.deselect()
    checkSET.deselect()
    
def inverttick():
    
    global checkinv
    checkinv=not checkinv



# TKINTER INTERFACE:    

root= Tk()
root.withdraw()
root.resizable(0, 0)
root.wm_attributes("-topmost", 1)
root.geometry("540x620")
root.iconbitmap('favicon.ico')


buttonb=Button(root, height=2, width=15, text='-START/PAUSE- \n(numpad 0)', command=lambda:motor.pause())
buttonb.grid(row = 2, column = 1,pady=10)

buttonserial=Button(root,height=1, width=8,text='CONNECT', command=lambda:serialstart(comtext.get(), serialbaud))
buttonserial.grid(row = 0, column = 2)

buttonabout=Button(root,height=1, width=8,text='About...', command=lambda:about())
buttonabout.grid(row = 0, column = 5)


checkontop=Checkbutton(root,text = 'On top', command=lambda:alwaysONtop())
checkontop.grid(row = 0, column = 3, sticky=W)
checkontop.select()


comtext = StringVar()
comentry=Entry(root, textvariable=comtext)
comentry.grid(row = 0, column = 1)

labe = Label(root, text="COM:")
labe.grid(row = 0, column = 0)

checkAOVar = IntVar()
checkAO=Checkbutton(root,text = 'ALWAYS ON', command=lambda:alwaysONtick(), variable = checkAOVar)
checkAO.grid(row = 2, column = 2, sticky=W)

checkDETVar = IntVar()
checkDET=Checkbutton(root,text = 'DETECT', command=lambda:detecttick(), variable = checkDETVar)
checkDET.grid(row = 2, column = 4, sticky=W)

checkSETVar = IntVar()
checkSET=Checkbutton(root,text = 'DETECT SETUP', command=lambda:detectsetup(), variable = checkSETVar)
checkSET.grid(row = 2, column = 5, sticky=W)

checkPULVar = IntVar()
checkPUL=Checkbutton(root,text = 'PULSE', command=lambda:pulsetick(), variable = checkPULVar)
checkPUL.grid(row = 2, column = 3, sticky=W)

motorspeed=IntVar(value=10)
slidera = Scale(root, from_=0, to=255, orient=HORIZONTAL,length=400.00, variable=motorspeed, label='MOTOR SPEED:', command=speedslider)
slidera.grid(columnspan = 6,pady=5)
speed=(str(motorspeed.get()))

timeON=IntVar(value=100)
sliderb = Scale(root, from_=20, to=1000, orient=HORIZONTAL,length=400.00, variable=timeON, label='TIME ON(ms):', command=timeONslider)
sliderb.grid(columnspan = 7,pady=5)
timeonvar=timeON.get()

timeOFF=IntVar(value=100)
sliderc = Scale(root, from_=20, to=1000, orient=HORIZONTAL,length=400.00, variable=timeOFF, label='TIME OFF(ms):', command=timeOFFslider)
sliderc.grid(columnspan = 8,pady=5)
timeoffvar=timeOFF.get()

floorspeedVAR=IntVar(value=0)
sliderd = Scale(root, from_=0, to=255, orient=HORIZONTAL,length=400.00, variable=floorspeedVAR, label='FLOOR SPEED:', command=floorspeedslider)
sliderd.grid(columnspan = 9,pady=5)
floorspeed=str(floorspeedVAR.get())

sizex=IntVar(value=25)
slidersizex = Scale(root, from_=1, to=100, orient=HORIZONTAL,length=400.00, variable=sizex, label='Xsize:', command=slidersize)
slidersizex.grid(columnspan = 10,pady=5)
xsize=sizex.get()*(streamwindowssizex - 20)/200
    
sizey=IntVar(value=25)
slidersizey = Scale(root, from_=1, to=100, orient=HORIZONTAL,length=400.00, variable=sizey, label='Ysize:', command=slidersize)
slidersizey.grid(columnspan = 11,pady=5)
ysize=sizey.get()*(streamwindowssizey - 20)/200

tresh=IntVar(value=70)
slidertresh = Scale(root, from_=1, to=100, orient=HORIZONTAL,length=400.00, variable=tresh, label='TRESHOLD:', command=tresholdslider)
slidertresh.grid(columnspan = 12,pady=5)
treshold=int(tresh.get())/100

checkinv=False
checkinvert=Checkbutton(root,text = 'Invert', command=inverttick)
checkinvert.grid(columnspan = 13)

root.protocol("WM_DELETE_WINDOW", on_closing)
root.title('CHM ' + version)


#THREAD:

motor=motorclass()
tmotordetect=threading.Thread(target=motor.detect, args=())
tmotordetect.setDaemon(True)
tmotordetect.start()


#INITIALIZING:
arduino=None
print('CHMACHINE Ver. %s \n' %version)
keysetup('setup.txt') #assign keys from setup.txt

print('- HOTKEYS:\n')
print('Pause=',pausebutton)
print('Slow down=',slowdownbutton)
print('Speed up=',speedupbutton)
print('Screenshot=',screenshotbutton)
print('Screenshot update=',refreshbutton)
print('')
print('') 


comportsetup() #list all available com ports
pos=None
pygame.init()
hm = pyHook.HookManager() # hooking keyboard
hm.KeyDown = onKeyDown
hm.HookKeyboard() 
pygame.event.pump()
root.deiconify()
root.mainloop()





    

    

