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
from win32api import GetSystemMetrics
import ctypes

try:

    ctypes.windll.user32.SetProcessDPIAware()# Make the application DPI aware to accommodate 4K resolution

except:
    pass

version = '0.9.3'

serialbaud=9600
streamwindowssizex=220
streamwindowssizey=220
Clock = pygame.time.Clock()
Clock.tick()

def keysetup(file):
    global pausebutton
    global slowdownbutton
    global speedupbutton
    global screenshotbutton
    global refreshbutton
    linelist=[]

    #default keys:
    pausebutton='Numpad0'
    slowdownbutton='Numpad1'
    speedupbutton='Numpad2'
    screenshotbutton='F9'
    refreshbutton='F10'

    try:
        setup  = open(file, 'r')

        for x in range(100):
            linelist=setup.readline().replace(' ', '').strip().split('=') #read line, remove spaces and split the string a the "=" sign
            #print (linelist)

            if linelist[0]== '***':     
                break
            if linelist[0] == 'Pause':
                pausebutton=linelist[1]

            if linelist[0] == 'Slowdown':
                slowdownbutton=linelist[1]
    
            if linelist[0] == 'Speedup':
                speedupbutton=linelist[1]

            if linelist[0] == 'Screenshot':
                screenshotbutton=linelist[1]
        
            if linelist[0] == 'Refresh':
                refreshbutton=linelist[1]


        setup.close() 
    except:
        print('Cannot open', file, ', loading default keys...\n')

        
def patternsetup(file):

    global namelist
    global patternlist

    linelist=[]
    namelist=[]
    patternlist=[]
    namelist.append('PATTERN')
    namelist.append('None')
    patternlist.append([0])
    patternlist.append([0])
    try:
        patterntxt = open(file, 'r')    

        for x in range(100):
            linelist=patterntxt.readline()        

            if linelist.strip()== '***':#strip() removes white spaces and end of line characters
                break

            try:

                if linelist.count('=')==1 and linelist.count(':')>0:
                    linelist=linelist.replace(' ', '').replace(',', '.').strip().split('=') #read line, remove spaces, convert "," to "." and split the string at the "=" sign
                        
           

                    if linelist[0] != '' and linelist[1]!= '':
                        namelist.append(linelist[0][0:18])
                        stringlist=linelist[1].split(':')
                        intlist = [int(round(float(i))) for i in stringlist]#converts list of strings into rounded integers
                        patternlist.append(intlist)
                        

            except:
                print(file, 'FORMAT ERROR\n')

        patterntxt.close() 
    except:
        print('Cannot open', file, '\n')


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
        self.keepalivems=100
        self.result=0 
        self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create an array of zeros for the black background
        self.index=0
        self.listindex=0
        self.timetic=0
        self.patternspeed=0
        self.speed='0'
        self.pinresttime=0

    def detect(self):
        

        while 1:
           
            while (self.state==5) or (self.state==1): #################### DETECT

                if self.state==5 and self.getspeed()!='0':

                    self.PWMpin('0')
                   
                arr = np.array(ImageGrab.grab(bbox=((pos[0]-xsize),(pos[1]-ysize),(pos[0]+xsize),(pos[1]+ysize))))
                arr = cv2.cvtColor(arr,cv2.COLOR_RGB2BGR)
                self.result = cv2.matchTemplate(arr, arrbase, cv2.TM_CCOEFF_NORMED)

                try:#take care of sliding too fast which result in a shape out of boundaries

                    if self.state==5:

                        if self.result>0:
                            print ('%.0f %% Match' %(self.result*100))
                        else:
                            print ('0 % Match')

                    
                    if checkinv==False: #invert flag False
                       
                        if (self.result>=treshold):#turn on the pin if the match value is over the threshold

                            if self.state==1:
                                self.PWMpin(speed)
                            
                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background
                            cv2.circle(self.colorshow,(0,0), 63, (0,255,0), -1) #draw a green circle
                            self.tempo=pygame.time.get_ticks()
                    
                        elif (pygame.time.get_ticks()-self.tempo) >= (timeonvar):  #turn the pin to floor speed some time after the last match is occurred 

                            if self.state==1:
                                self.PWMpin(floorspeed)

                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background

                         

                    else: #invert flag True
                    
                        if (self.result<=treshold):#turn on the pin if the match value is under the threshold

                            if self.state==1:
                                self.PWMpin(speed)

                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background
                            cv2.circle(self.colorshow,(0,0), 63, (0,255,0), -1) #draw a green circle
                            self.tempo=pygame.time.get_ticks()
                    
                        elif (pygame.time.get_ticks()-self.tempo) >= (timeonvar):  #turn off the pin to floor speed some time after the last match is occurred 
                            
                            if self.state==1:
                                self.PWMpin(floorspeed)

                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background

                    #centering and overlapping images over background:
                    x_offset=int(streamwindowssizex/2 - xsize) 
                    y_offset=int(streamwindowssizey/2 - ysize) 
                    self.colorshow[y_offset:y_offset + arr.shape[0], x_offset:x_offset + arr.shape[1]] = arr   
                
                except:
                    pass
                   
                        
                cv2.imshow('Stream', self.colorshow)  #showing image
                cv2.waitKey(1)

                if  pygame.time.get_ticks()-self.tempokeepalive>=self.keepalivems: #keeps the pin alive(see arduino code)

                    self.PWMpin(self.getspeed()) 
                    self.tempokeepalive=pygame.time.get_ticks()


            
            while self.state==2:#################### STOP/PAUSE

                if motor.getspeed()!='0': 
                    self.pinresttime=0
                    self.PWMpin('0')

                pygame.time.wait(1)


            while self.state==3: ##################### ALWAYS ON
                
                self.PWMpin(speed)
                pygame.time.wait(1)


            while self.state==4:######################### PULSE
                
                self.tempo=pygame.time.get_ticks()
                

                while (pygame.time.get_ticks()-self.tempo) <= (timeonvar):
                    if self.state!=4:
                        break
                    self.PWMpin(speed)
                    pygame.time.wait(1)
                    

                self.tempo=pygame.time.get_ticks()
                

                while (pygame.time.get_ticks()-self.tempo) <= (timeoffvar):
                    if self.state!=4:
                        break
                    self.PWMpin(floorspeed)
                    pygame.time.wait(1)
                    
                    
                

            while self.state==6: ##################### PATTERN
                
                self.listindex=namelist.index(patternvar)

                if pygame.time.get_ticks()-self.timetic>=timeonvar/100:
                    if self.index < len(patternlist[self.listindex])-1:
                        self.index+=1
                    else:
                        self.index=0
                    
                    self.patternspeed=int(round(patternlist[self.listindex][self.index]/100*int(speed)))
                    

                    if self.patternspeed>=int(floorspeed):
                        self.PWMpin(str(self.patternspeed))
                        #print(self.patternspeed)

                    if self.patternspeed<int(floorspeed) and self.listindex>1:
                        self.PWMpin(floorspeed)
                        #print(self.patternspeed,floorspeed )


                    self.timetic=pygame.time.get_ticks()
                    
                

                     
    def getspeed(self):
        return self.speed


                              
    def PWMpin(self, PWM_speed): #set the PWM of the microcontroller pin
        self.speed=PWM_speed

        try:

            if (pygame.time.get_ticks()-self.pinresttime) > 5: #limit serial flooding
                arduino.write(('V' + self.speed + 'S').encode('utf-8'))
                self.pinresttime=pygame.time.get_ticks()

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

    def pattern(self):
        self.state=6
        self.savestate=self.state

 
def serialstartauto(baud): 
    checkAO.configure(state=DISABLED)
    checkPUL.configure(state=DISABLED)
    checkDET.configure(state=DISABLED)
    checkSET.configure(state=DISABLED)
    checkpatterntick.configure(state=DISABLED)
    buttonserial.configure(state=DISABLED)
    comentry.insert(END, "PLEASE WAIT...") # insert text into the widget
    comentry.configure(state=DISABLED)

    global arduino
    line=('')
    portnumber=('')
    comentry.delete(0, END)  # delete text from the widget from position 0 to the END 
    root.focus() #remove focus from the entry widget
    
    
    resetGUI()
    motor.stop() 
         

    print("Looking for the CH Machine, PLEASE WAIT...\n")
    for p in ports: 
        
        try:
            try:#close already existing serial connection
                arduino.close()
                while arduino.is_open:
                    pygame.time.wait(1)
            except:
               pass

            print (p[0] + '...')
            arduino = serial.Serial(p[0], baud, timeout = 1, write_timeout = 1) # 2=Com3 on windows always a good idea to specify a timeout in case we send bad data
            while arduino.is_open==False:
                    pygame.time.wait(1)# wait for arduino to initialize

            arduino.write(('T').encode('utf-8'))#
            pygame.time.wait(150)
            line = arduino.read(arduino.inWaiting()).decode(encoding='UTF-8',errors='replace')   
            if line.find('connOK')!=-1:#
                print("CHM CONNECTED!")
                print (p[0] + ' - Initialization Complete.')
                break
            else:
                print ('Wrong serial connection.')
                   
        except:
            print ('Serial port exception')

    if line.find('connOK')==-1:
        print ('\nCH Machine NOT found, check out the connection.\n')

    checkAO.configure(state=NORMAL)
    checkPUL.configure(state=NORMAL)
    checkDET.configure(state=NORMAL)
    checkSET.configure(state=NORMAL)
    checkpatterntick.configure(state=NORMAL)
    buttonserial.configure(state=NORMAL)
    comentry.configure(state=NORMAL)
    comentry.delete(0, END) 
    

    return True


def serialstart(COMstring, baud):
    global arduino
    line=('')
    comentry.delete(0, 'end')  # delete text from the widget  
    root.focus() #remove focus from the entry widget
    
    
    if COMstring ==(''): #start serialstartauto() to find correct COM port
        tserial=threading.Thread(target=serialstartauto, args={serialbaud})
        tserial.setDaemon(True)
        tserial.start()

    
        
    #manual COM port:
    elif COMstring.isdigit()==True:

        print ('COM' + COMstring + ' - Initializing...')
        resetGUI()
        motor.stop()   
         
        try:
            arduino.close()
            while arduino.is_open:
                    pygame.time.wait(1)
        except:
            pass

        try:
            arduino = serial.Serial(('COM' + str(COMstring)), baud, timeout = 1, write_timeout = 1) # 2=Com3 on windows always a good idea to specify a timeout in case we send bad data
            while arduino.is_open==False:
                pygame.time.wait(1)# wait for arduino to initialize
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
        if (checkAOVar.get()==True or checkPULVar.get()==True or checkDETVar.get()==True or checkpatternVar.get()==True):
            if speedint>10:
                speedint -= 10
                motorspeed.set(speedint)
                speed=str(speedint)
                
            else:
                motorspeed.set(0)
                speed=('0')
                


    if event.Key == (speedupbutton): 
        speedint=int(speed)
        if (checkAOVar.get()==True or checkPULVar.get()==True or checkDETVar.get()==True or checkpatternVar.get()==True):
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



def alwaysONtick():
    
    
    try:
        arduino.name
        if (arduino.is_open):
            


            if checkAOVar.get()==False:
                resetGUI()
                motor.stop()

       
            if checkAOVar.get()==True:
                resetGUI()
                slidera.config(foreground='black')
                checkAO.select()
                motor.alwayson()
        else:
            print('No serial connection')
            checkAO.deselect()
    except:
        print('No serial connection')
        checkAO.deselect()


def patterntick():
     
     try:
        arduino.name
        if (arduino.is_open):
     
            if checkpatternVar.get()==False:
                resetGUI()
                motor.stop()
        
           
         
            if checkpatternVar.get()==True:
                resetGUI()
                slidera.config(foreground='black')
                sliderb.config(foreground='black', label='PATTERN FREQ:')
                sliderd.config(foreground='black')
                checkpatterntick.select()
                motor.pattern()

        else:
            print('No serial connection')
            checkpatterntick.deselect()

     except:
        print('No serial connection')
        checkpatterntick.deselect()


def detecttick():
     
 
     if (pos==None):
            print('Position? (Press', screenshotbutton, 'to take a screenshot)')
            checkDET.deselect()
            

     else:
        try:
            arduino.name
            if (arduino.is_open):
        
                if checkDETVar.get()==False:
                    resetGUI()
                    motor.stop()
        
                if checkDETVar.get()==True:
                    resetGUI()
                    slidera.config(foreground='black')
                    sliderb.config(foreground='black')
                    sliderd.config(foreground='black')
                    slidersizex.config(foreground='black')
                    slidersizey.config(foreground='black')
                    slidertresh.config(foreground='black')
                    checkinvert.config(foreground='black')
                    checkDET.select()
                    motor.startdetect()
            else:
                print('No serial connection')
                checkDET.deselect()
        except:
            print('No serial connection')
            checkDET.deselect()

       
def detectsetup():
     

     if (pos==None):
            print('Position? (Press', screenshotbutton, 'to take a screenshot)')
            checkSET.deselect()

     else:
              

        if checkSETVar.get()==False:
            resetGUI()
            motor.stop()

        if checkSETVar.get()==True:
            resetGUI()
            sliderb.config(foreground='black')
            slidersizex.config(foreground='black')
            slidersizey.config(foreground='black')
            slidertresh.config(foreground='black')
            checkinvert.config(foreground='black')
            checkSET.select()
            motor.setup()


def pulsetick():
    try:
        arduino.name
        if (arduino.is_open):


            if checkPULVar.get()==False:
                resetGUI()
                motor.stop()
        
            if checkPULVar.get()==True:
                resetGUI()
                slidera.config(foreground='black')
                sliderb.config(foreground='black')
                sliderc.config(foreground='black')
                sliderd.config(foreground='black')
                checkPUL.select()
                motor.pulse()
        else:
            print('No serial connection')
            checkPUL.deselect()
    except:
        print('No serial connection')
        checkPUL.deselect()


def on_closing():

    print ('Bye Bye')
    motor.stop()

    try:
        arduino.close()
    except:
        pass

    root.destroy()
    print ('Be vigilant')
    sys.exit()


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
    checkpatterntick.deselect()

    slidera.config(foreground='gray')
    sliderb.config(foreground='gray', label='TIME ON(ms):')
    sliderc.config(foreground='gray')
    sliderd.config(foreground='gray')
    slidersizex.config(foreground='gray')
    slidersizey.config(foreground='gray')
    slidertresh.config(foreground='gray')
    checkinvert.config(foreground='gray')

  
def inverttick():
    
    global checkinv
    checkinv=not checkinv


def patternmenu(value):
    
    global patternvar
    patternvar=value
    



# TKINTER INTERFACE:    

root= Tk()
root.withdraw()
root.wm_attributes("-topmost", 1)

if GetSystemMetrics(0) < 3840 and GetSystemMetrics(1) < 2160: 
    root.resizable(0, 0)
    root.geometry("540x650")

else:# 4k and higher resolutions
    root.resizable(1, 1)
    root.geometry("1024x1080")

root.iconbitmap('favicon.ico')


buttonb=Button(root, height=2, width=15, text='-PAUSE/START- \n(numpad 0)', command=lambda:motor.pause())
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
checkAO.grid(row = 2, column = 2)

checkpatternVar = IntVar()
checkpatterntick=Checkbutton(root,text = '', command=lambda:patterntick(), variable = checkpatternVar)
checkpatterntick.grid(row = 3, column = 1, sticky=E)

patternsetup('pattern.txt')#load patterns
patternvar='None'
pattern_variable = StringVar()
pattern_variable.set("PATTERN")
optionmenu_widget = OptionMenu(root, pattern_variable, *namelist[1:], command=patternmenu)
optionmenu_widget.grid(row = 3, column=2, columnspan=2, sticky=W+E)

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

timeON=IntVar(value=500)
sliderb = Scale(root, from_=10, to=1000, orient=HORIZONTAL,length=400.00, variable=timeON, label='TIME ON(ms):', command=timeONslider)
sliderb.grid(columnspan = 7,pady=5)
timeonvar=timeON.get()

timeOFF=IntVar(value=100)
sliderc = Scale(root, from_=10, to=1000, orient=HORIZONTAL,length=400.00, variable=timeOFF, label='TIME OFF(ms):', command=timeOFFslider)
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
resetGUI()

#THREADS:

motor=motorclass()
tmotordetect=threading.Thread(target=motor.detect, args=())
tmotordetect.setDaemon(True)
tmotordetect.start()

#INITIALIZING:
arduino=None
print('CHMACHINE Ver. %s \n' %version)
keysetup('setup.txt') #assign keys from setup.txt
Clock.tick()


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





    

    

