import cv2
import numpy as np
from tkinter import *
from PIL import ImageGrab, ImageTk, Image
import win32gui
import win32con
import win32console
import pyHook # pyhook_py3k is advised
import serial
import threading
import serial.tools.list_ports
import pygame
from win32api import GetSystemMetrics
import ctypes
import glob
import webbrowser
import pyperclip

debug=False
version = '0.9.5'
print('CHMACHINE Ver. %s \n' %version)

class motorclass():
    
    def __init__(self):
        self.state=2
        self.tempo=0
        self.savestate=2
        self.result=0 
        self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create an array of zeros for the black background
        self.index=0
        self.srt_index=0
        self.previous_srt_index=-1
        self.listindex=0
        self.timetic=0
        self.srt_time_zero=0
        self.patternspeed=0
        self.speed='0'
        self.targetspeed='0'
        self.pinresttime=0
        self.serialfloodlimit=100 #time(ms) between commands to limit serial flooding

                    


    def detect(self):

        while 1:  
            
            if arduino_connected==False:  
                 
                pygame.time.wait(1)                                                        
           
            while ((self.state==5) or (self.state==1)): #################### DETECT/DETECT SETUP

                if self.state==5 and self.getspeed()!=0 and arduino_connected==True:#turn off motor when entering setup mode

                    self.PWMpin('0')

                try:
                      
                    arr = np.array(ImageGrab.grab(bbox=((pos[0]-xsize/2),(pos[1]-ysize/2),(pos[0]+xsize/2),(pos[1]+ysize/2)))) #grab image on the screen
                    arr = cv2.cvtColor(arr,cv2.COLOR_RGB2BGR)
                    self.result = cv2.matchTemplate(arr, arrbase, cv2.TM_CCOEFF_NORMED) #check if images match

                except:

                    if debug==True:
                        print('matchTemplate error')

                try: #take care of sliding too fast which result in a shape out of boundaries

                    if self.state==5:

                        if self.result>0:
                            print ('%.0f %% Match' %(self.result*100))
                        else:
                            print ('0 % Match')

                    
                    if checkinv==False: #invert flag False


                        if (self.result>=threshold): # if match value is over the threshold

                            if self.state==1 and arduino_connected==True: 
                                self.PWMpin(speed)
                            
                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background
                            cv2.circle(self.colorshow,(0,0), 70, (0,255,0), -1) #draw a green circle 
                            self.tempo=pygame.time.get_ticks()
                    
                        elif (pygame.time.get_ticks()-self.tempo) >= (timeonvar):  #turn the pin to floor speed some time after the last match is occurred 

                            if self.state==1 and arduino_connected==True: 
                                self.PWMpin(floorspeed)
                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background
                            

                    else: #invert flag True
                    
                        if (self.result<=threshold):#match if value is under the threshold

                            if self.state==1 and arduino_connected==True:
                                self.PWMpin(speed)

                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background
                            cv2.circle(self.colorshow,(0,0), 70, (0,255,0), -1) #draw a green circle 
                            self.tempo=pygame.time.get_ticks()
                    
                        elif (pygame.time.get_ticks()-self.tempo) >= (timeonvar):  #turn the pin to floor speed some time after the last match is occurred 
                            
                            if self.state==1 and arduino_connected==True:
                                self.PWMpin(floorspeed)

                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #create a black background
                            

                    #centering and overlapping images over background:
  
                    x_offset=int((streamwindowssizex - xsize)/2)
                    y_offset=int((streamwindowssizey - ysize)/2)
                    self.colorshow[y_offset:y_offset + arr.shape[0], x_offset:x_offset + arr.shape[1]] = arr   
                
                except:
                    if debug==True:
                        print('streamwindow error')
                   
                hwndstream = win32gui.FindWindow(None,'Stream')
                if hwndstream!=0: #if "Stream" window is open
                    
                    cv2.imshow('Stream', self.colorshow)  #show image
                    cv2.waitKey(1)
                
                if self.state==1 and arduino_connected==True:
                    self.PWMpin(str(self.getspeed())) #Keeps the PWM pin alive (see Arduino code)
                   


            
            while (self.state==2 or self.state==6) and arduino_connected==True:#################### STOP/PAUSE
                

                self.PWMpin('0')
                pygame.time.wait(1)


            while self.state==3 and arduino_connected==True: ##################### ALWAYSON/PATTERN
      

                if '.srt' in patternvar:    # srt sequence               

                    try:

                        if (pygame.time.get_ticks() >= srt_data[0][self.srt_index + 1] + self.srt_time_zero + shiftms 
                            and srt_data[0][self.srt_index + 1] != -1): #last element of list is -1

                            self.srt_index += 1

                        if pygame.time.get_ticks() >= srt_data[1][self.srt_index] + self.srt_time_zero+ shiftms:

                            self.PWMpin(floorspeed)

                        elif pygame.time.get_ticks() >= srt_data[0][self.srt_index] + self.srt_time_zero + shiftms:
                            
                            if self.srt_index != self.previous_srt_index:

                                print(srt_data[3][self.srt_index], srt_data[2][self.srt_index],'%')
                                self.previous_srt_index = self.srt_index

                            self.PWMpin(str(int(srt_data[2][self.srt_index] / 100* int(speed))))       

                        pygame.time.wait(1)
                        
                    except:
                       
                        self.PWMpin('0')
                        if debug==True:

                            print('srt list index out of range')

                elif patternvar=='none':
                    
                    self.PWMpin(speed)
                    pygame.time.wait(1)
                
                else: #patterns
                    
                    self.listindex=namelist.index(patternvar)

                    if pygame.time.get_ticks()-self.timetic>=timeonvar/100:
                        if self.index < len(patternlist[self.listindex])-1:
                            self.index+=1
                        else:
                            self.index=0
                    
                        self.patternspeed=int(round(patternlist[self.listindex][self.index]/100*int(speed)))
                    

                        if self.patternspeed>=int(floorspeed):
                            self.PWMpin(str(self.patternspeed))

                        if self.patternspeed<int(floorspeed) and self.listindex>1:
                            self.PWMpin(floorspeed)


                        self.timetic=pygame.time.get_ticks()
                        pygame.time.wait(1)


            while self.state==4 and arduino_connected==True:######################### PULSE
                
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
                    

                

                     
    def getspeed(self):
        return int(self.speed)



    def PWMpin(self, PWM_speed): #set the Arduino pin PWM
        global arduino_connected


        try:

            if ((pygame.time.get_ticks()-self.pinresttime) > self.serialfloodlimit #limit serial flooding
                or PWM_speed != self.speed): 

                self.speed=PWM_speed
                arduino.write(('V' + self.speed + 'S').encode('utf-8'))
                self.pinresttime=pygame.time.get_ticks()

        except serial.SerialTimeoutException: 
            print('WRITE TIMEOUT ERROR.')
            arduino.close()
            self.stop()
            arduino_connected=False
           
        except:
            print('SERIAL CONNECTION ERROR')
            arduino.close()
            self.stop()
            arduino_connected=False



    def stop(self):
        self.state=2
        self.savestate=2


    def pause(self):
       
        if self.state!=2 and self.state!=6:
            
            self.savestate=self.state
            self.state=2
            

        elif self.state==6:#srt stopped routine starts again
            
            self.srt_time_zero = pygame.time.get_ticks() - srt_data[0][self.srt_index]
            self.state=3

        elif self.state==2:

            try:  #restart paused SRT routine and catch up to the current position           

                while pygame.time.get_ticks() >= srt_data[0][self.srt_index] + self.srt_time_zero + shiftms: 
                    self.srt_index += 1
            except:
                if debug==True:
                        print('SRT catch-up error')
                
            self.state=self.savestate
            
        

    def startdetect(self):
        self.state=1
        self.savestate=self.state

    def skipsrt(self,skip):
        try:

            if self.state!=6:
                self.savestate=self.state
                self.state=6
                print('GAME PAUSED') 
             
            if skip == 1 and self.srt_index < len(srt_data[3]):   

                self.srt_index += 1 
                print(srt_data[3][self.srt_index])
                self.srt_time_zero = pygame.time.get_ticks() - srt_data[0][self.srt_index]
             

            elif skip == -1 and self.srt_index>0:

                self.srt_index -= 1 
                print(srt_data[3][self.srt_index])
                self.srt_time_zero = pygame.time.get_ticks() - srt_data[0][self.srt_index]
        except:

            if debug==True:
                        print('SRT skip error')
            
            
           

    def alwayson_pattern(self):
        global shiftms
        self.state=3
        self.savestate=self.state
        self.timetic=pygame.time.get_ticks()
        self.srt_time_zero=pygame.time.get_ticks()
        self.srt_index=0
        self.previous_srt_index=-1
        shiftms=0


    def pulse(self):
        self.state=4
        self.savestate=self.state

    def setup(self):
        self.state=5
        self.savestate=self.state


def keysetup(file):
    global pausebutton
    global slowdownbutton
    global speedupbutton
    global screenshotbutton
    global refreshbutton
    global savebutton
    global loadbutton
    global timer_up_button
    global timer_down_button
    global next_srt_button
    global previous_srt_button

    linelist=[]

    ###default keys:
    pausebutton='Numpad0'
    slowdownbutton='Numpad1'
    speedupbutton='Numpad2'
    screenshotbutton='F9'
    refreshbutton='F10'
    savebutton='F11'
    loadbutton='F12'
    timer_down_button='Numpad4'
    timer_up_button='Numpad5'
    next_srt_button='Numpad8'
    previous_srt_button='Numpad7'
    ###

    try:
        setup  = open(file, 'r')
        while 1:
            
            linelist=setup.readline().replace(' ', '').strip().split('=') #read line, remove spaces and split the string a the "=" sign
            
            if (not linelist) or linelist[0]== '***': # stop when it reaches end of file or '***' string
                setup.close()
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
             
            if linelist[0] == 'Loadstate':
                loadbutton=linelist[1]

            if linelist[0] == 'Savestate':
                savebutton=linelist[1]

            if linelist[0] == 'SRT_shift_up':
                timer_up_button=linelist[1]

            if linelist[0] == 'SRT_shif_down':
                timer_down_button=linelist[1]

            if linelist[0] == 'SRT_next_event':
                next_srt_button=linelist[1]

            if linelist[0] == 'SRT_previus_event':
                previous_srt_button=linelist[1]

    except:
        print('Cannot open', file, ', loading default keys...\n')

    print('- HOTKEYS:\n')
    print('Pause --------------- ',pausebutton)
    print('Slow down ----------- ',slowdownbutton)
    print('Speed up ------------ ',speedupbutton)
    print('Screenshot ---------- ',screenshotbutton)
    print('Screenshot update --- ',refreshbutton)
    print('Save state ---------- ',savebutton)
    print('Load state ---------- ',loadbutton)
    print('SRT shift +10ms ----- ',timer_up_button)
    print('SRT shift -10ms ----- ',timer_down_button)
    print('SRT next event ------ ',next_srt_button)
    print('SRT previous event -- ',previous_srt_button)
    print('')
    print('') 


def srtsetup():# load srt file names into the list

    global namelist

    filesname=glob.glob("*.srt") #find name of all .srt files in the main folder
    for x in range(len(filesname)):
        namelist.append(filesname[x])

     
def srtselect(selection):# load srt data

    global srt_data
    srt_time=[]
    srt_startms=[]
    srt_endms=[]
    srt_speed=[]
    srt_data=[srt_startms, srt_endms, srt_speed, srt_time]
               
    file=open(selection, 'r')        
    while 1:

        linelist=file.readline() 
        if not linelist: # stop when it reaches end of file

            file.close()            
            srt_startms.append(-1)
            break

        if linelist.count('-->')>0:
            srt_time.append(linelist)
            linelist=linelist.replace(' ', '').replace('-', '').replace(',', ':').replace('>', ':').strip().split(':') #strip() removes end of line characters, split() method returns a list of strings after breaking the given string by the specified separator.
            starthour=int(linelist[0])*3600000
            startmin=int(linelist[1])*60000
            startsec=int(linelist[2])*1000
            startms=int(linelist[3]) + starthour + startmin + startsec
            srt_startms.append(startms)

            endhour=int(linelist[4])*3600000
            endmin=int(linelist[5])*60000
            endsec=int(linelist[6])*1000
            endms=int(linelist[7]) + endhour + endmin + endsec
            srt_endms.append(endms)

            linelist=file.readline().replace(' ', '').strip()              
            if linelist.isdigit():
                if int(linelist)>100:
                    linelist='100'
                srt_speed.append(int(linelist))

        
def patternsetup(file):

    global namelist
    global patternlist

    linelist=[]
    patternlist=[]
    namelist.append('PATTERN')
    namelist.append('none')
    patternlist.append([0])
    patternlist.append([0])
    try:
        patterntxt = open(file, 'r')    

        while 1:
            linelist=patterntxt.readline()   
            
            if not linelist: # stop when it reaches end of file
                patterntxt.close()
                break   

            if linelist.strip()== '***':  #strip() removes white spaces and end of line characters
                break

            try:

                if linelist.count('=')==1 and linelist.count(':')>0:
                    linelist=linelist.replace(' ', '').replace(',', '.').strip().split('=') #read line, remove spaces, convert "," to "." and split the string at the "=" sign
                        
           

                    if linelist[0] != '' and linelist[1]!= '':
                        namelist.append(linelist[0][0:18])
                        stringlist=linelist[1].split(':')
                        intlist = [int(round(float(i))) for i in stringlist] #converts list of strings into rounded integers
                        patternlist.append(intlist)
                        

            except:
                print(file, 'FORMAT ERROR\n')

        patterntxt.close() 
    except:
        print('Cannot open', file, '\n')


def comportsetup():
    global ports
    ports = list(serial.tools.list_ports.comports()) # detects available ports
    print ('- AVAILABLE PORTS:\n') 
    for p in ports:
        print (p) 
    print('')

 
def autoserialstart(baud): 
    checkAO.configure(state=DISABLED)
    checkPUL.configure(state=DISABLED)
    checkDET.configure(state=DISABLED)
    checkSET.configure(state=DISABLED)
    buttonserial.configure(state=DISABLED)
    comentry.insert(END, "PLEASE WAIT...") # insert text into the widget
    comentry.configure(state=DISABLED)

    global arduino
    global arduino_connected
    line=('')
    portnumber=('')
    comentry.delete(0, END)  # delete text from the widget from position 0 to the END 
    root.focus() #remove focus from the entry widget
    
    
    resetGUI()
    motor.stop() 
        
    print("Looking for the CH Machine, PLEASE WAIT...\n")
    for p in ports: 
        arduino_connected=False

        try:#try to close already existing serial connection
                arduino.close()
                while arduino.is_open:
                    pygame.time.wait(1)
        except:
            if debug==True:
                        print('serial connection error')


        try:
                        
            print (p[0] + '...')
            arduino = serial.Serial(p[0], baud, timeout = 1, write_timeout = 1) # 2=Com3 on windows always a good idea to specify a timeout in case we send bad data
            pygame.time.wait(2000)# wait for arduino to initialize

            arduino.write(('T').encode('utf-8'))
            pygame.time.wait(150)
            line = arduino.read(arduino.inWaiting()).decode(encoding='UTF-8',errors='replace')   
            if line.find('connOK')!=-1:
                print("CHM CONNECTED!")
                print (p[0] + ' - Initialization Complete.')
                arduino_connected=True
                break
            else:
                print ('Wrong serial connection.')
                   
        except:
            print ('Serial port exception')

    if line.find('connOK')==-1:
        print ('\nCHMachine not found, check out the connection.\n')

    checkAO.configure(state=NORMAL)
    checkPUL.configure(state=NORMAL)
    checkDET.configure(state=NORMAL)
    checkSET.configure(state=NORMAL)
    buttonserial.configure(state=NORMAL)
    comentry.configure(state=NORMAL)
    comentry.delete(0, END) 
    

    return True


def serialstart(COMstring, baud):
    global arduino_connected
    global arduino
    line=('')
    comentry.delete(0, 'end')  # delete text from the widget  
    root.focus() #remove focus from the entry widget
     
    
    if COMstring == ('') or COMstring == ('COM Port'): #start autoserialstart() to find correct COM port
        tserial=threading.Thread(target=autoserialstart, args={serialbaud})
        tserial.setDaemon(True)
        tserial.start()

    
        
    #manual COM port:
    elif COMstring.isdigit()==True:

        print ('COM' + COMstring + ' - Initializing...')
        resetGUI()
        arduino_connected=False   
        motor.stop()   
                 
        
        try:#try to close already existing serial connection

            arduino.close()
            while arduino.is_open:
                pygame.time.wait(1)

        except:
            if debug==True:
                print('streamwindow error')            
        

        try:
            arduino = serial.Serial(('COM' + str(COMstring)), baud, timeout = 1, write_timeout = 1) # 2=Com3 on windows always a good idea to specify a timeout in case we send bad data
            pygame.time.wait(2000)# wait for the Arduino to initialize
            #test the connection(see Arduino code):
            arduino.write(('T').encode('utf-8'))
            pygame.time.wait(150)
            line = arduino.read(arduino.inWaiting()).decode(encoding='UTF-8',errors='replace')   
            if line.find('connOK')!=-1:
                print("CHM CONNECTED!")
                print ('COM' + str(COMstring) + ' - Initialization Complete.')
                arduino_connected=True
             
            else:
                print ('Wrong serial connection.')
                arduino.close()

        except serial.SerialTimeoutException:
            print ('COM' + COMstring + ' TIMEOUT EXCEPTION. Try another port.')
            arduino.close()
            arduino_connected=False
                
        except:
            if COMstring.isdigit()==True:
                print('COM' + COMstring +' - No port found.')
            else:
                print('No port found.')
                
    elif (COMstring !=('') and COMstring.isdigit()==False):
        print('Digits only')

     
def onKeyDown(event):
    
    global speed
    global pos
    global arrbase
    global savelist
    global loadlist
    global shiftms

# never put any condition before event.key 
    if event.Key == ('Return'):
        
        if comentry==root.focus_get() and comentry.get()!=(''):
            serialstart(comtext.get(), serialbaud)

    if event.Key == (next_srt_button):
        if checkAOVar.get()==True:
            motor.skipsrt(1)

    if event.Key == (previous_srt_button):
        if checkAOVar.get()==True:
            motor.skipsrt(-1)
      
    if event.Key == (timer_up_button): 
        print(shiftms,'shifted ms')
        shiftms+=10

    if event.Key == (timer_down_button): 
        print(shiftms,'shifted ms')
        shiftms-=10

    if event.Key == (slowdownbutton):
        
        speedint=int(speed)
        if (checkAOVar.get()==True or checkPULVar.get()==True or checkDETVar.get()==True):
            if speedint>10:
                speedint -= 10
                motorspeed.set(speedint)
                speed=str(speedint)
                
            else:
                motorspeed.set(0)
                speed=('0')
                


    if event.Key == (speedupbutton): 
        speedint=int(speed)
        if (checkAOVar.get()==True or checkPULVar.get()==True or checkDETVar.get()==True):
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
        
        if (event.Key == screenshotbutton):

            pos=win32gui.GetCursorPos()
                    
        if (pos != [-1,-1]):

            print(pos)  
            arrbase = np.array(ImageGrab.grab(bbox=((pos[0]-xsize/2),(pos[1]-ysize/2),(pos[0]+xsize/2),(pos[1]+ysize/2)))) #grab image on the screen
            arrbase = cv2.cvtColor(arrbase,cv2.COLOR_RGB2BGR)           
            base=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #an array of zeros for a black background
            x_offset=int((streamwindowssizex - xsize)/2)
            y_offset=int((streamwindowssizey - ysize)/2)
            base[y_offset:y_offset+arrbase.shape[0], x_offset:x_offset+arrbase.shape[1]] = arrbase #center the image array
            cv2.imshow('Match',base)
            cv2.namedWindow('Stream', cv2.WINDOW_AUTOSIZE)
            ontop()  
            cv2.waitKey(1)
                     

   
    if event.Key == (savebutton):

        filesname=glob.glob("*.npz") #find name of all .npz files in the main folder
        savelist=[]

        
        for x in filesname:
            try: #in case of a miswritten file name
                num=int(x.replace('save', '').replace('.npz', '')) #removes letters from string and converts number to int
                savelist.append(num)
            except:
                if debug==True:
                    print('filename error')

        if savelist!=[]:
            savename=('save' + str(max(savelist) + 1) + '.npz') #find the max value to add to the string
            
        else:
            savename=('save0.npz')

        np.savez(savename, arrbase, pos, int(xsize), int(ysize), speed, floorspeed, timeonvar, timeoffvar, threshold, checkinv)
        print(savename, 'SAVED')
        loadlist=[]

 

    if event.Key == (loadbutton):

        filesname=glob.glob("*.npz") #find name of all npz files in the main folder
        if loadlist==[]: 

            for x in filesname:
                try: #in case of a miswritten file name
                    num=int(x.replace('save', '').replace('.npz', '')) #removes letters from string and converts number to int
                    loadlist.append(num)
                except:
                    if debug==True:
                        print('filename error')
                
        loadlist.sort() #sort numbers in the list

        if loadlist!=[]: 

            loadname=('save' + str(loadlist.pop()) + '.npz') # pop() removes last element and return it
            loaded_arrays = np.load(loadname)

            load_state(loaded_arrays['arr_0'], loaded_arrays['arr_1'], loaded_arrays['arr_2'], loaded_arrays['arr_3'], loaded_arrays['arr_4'],
                       loaded_arrays['arr_5'], loaded_arrays['arr_6'], loaded_arrays['arr_7'], loaded_arrays['arr_8'], loaded_arrays['arr_9'])
            print(loadname, 'LOADED')
        else:
            print('nothing to load')
           
   

        
    return True


def load_state(image_arrayl, posl, xsizel, ysizel, speedl, floorspeedl, timeonvarl, timeoffvarl, thresholdl, checkinvl):
    
    global xsize
    global ysize
    global speed
    global timeonvar
    global timeoffvar
    global floorspeed
    global threshold
    global arrbase
    global pos
    global checkinv

    ###load variables and update interface:

    motorspeed.set(speedl) 
    speed=str(speedl)

    timeON.set(timeonvarl)
    timeonvar=timeON.get()

    timeOFF.set(timeoffvarl)
    timeoffvar=timeOFF.get()

    floorspeedVAR.set(floorspeedl)
    floorspeed=str(floorspeedVAR.get())

    thresh.set(thresholdl * 100)
    threshold=thresholdl

    if checkinvl == True:
        checkinvert.select()
        checkinv=True
    else:
        checkinvert.deselect()
        checkinv=False
    

    ###load image:

    if posl[0] != -1:

        pos = [posl[0], posl[1]]
        arrbase=image_arrayl
        sizex.set(int(xsizel/2))
        sizey.set(int(ysizel/2))
        xsize=xsizel/2*(streamwindowssizex - 20)/100
        ysize=ysizel/2*(streamwindowssizey - 20)/100
        x_offset=int((streamwindowssizex - xsize)/2)
        y_offset=int((streamwindowssizey - ysize)/2)
        base=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #an array of zeros for a black background
        base[y_offset:y_offset+arrbase.shape[0], x_offset:x_offset+arrbase.shape[1]] = arrbase #center the image array
        cv2.imshow('Match', base)
        cv2.namedWindow('Stream', cv2.WINDOW_AUTOSIZE)
        cv2.waitKey(1)
    ###


# TKINTER FUNCTIONS:


def alwaysONtick():
    
        try:
            arduino.name
            if (arduino.is_open):
            


                if checkAOVar.get()==False:
                    resetGUI()
                    motor.stop()

       
                if checkAOVar.get()==True:

                    if patternvar=='none':

                        resetGUI()
                        slidera.config(foreground='black')
                        checkAO.select()
                        motor.alwayson_pattern()


                    else:
                      
                        resetGUI()
                        if '.srt' in patternvar:
                            sliderb.config(foreground='gray') 
                        else:
                            sliderb.config(foreground='black', label='PATTERN FREQ:')

                        slidera.config(foreground='black')                        
                        sliderd.config(foreground='black')
                        checkAO.select()
                        motor.alwayson_pattern()

            else:
                print('No serial connection')
                checkAO.deselect()
        except:
            print('EXCEPTION: No serial connection')
            checkAO.deselect()


def detecttick():
     
     if (pos==[-1,-1]):
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
                    sliderthresh.config(foreground='black')
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
     

     if (pos==[-1,-1]):
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
            sliderthresh.config(foreground='black')
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
    root.quit()
    root.destroy()
    cv2.destroyAllWindows()
    print ('Be vigilant')
    sys.exit()


def slidersize(value):
    global arrbase
    global xsize
    global ysize

    xsize=sizex.get()*(streamwindowssizex - 20)/100
    ysize=sizey.get()*(streamwindowssizey - 20)/100

    if pos != [-1,-1]:

        arrbase = np.array(ImageGrab.grab(bbox=((pos[0]-xsize/2),(pos[1]-ysize/2),(pos[0]+xsize/2),(pos[1]+ysize/2)))) #grab image on the screen
        arrbase=cv2.cvtColor(arrbase,cv2.COLOR_RGB2BGR) 
        base=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #an array of zeros for a black background
        x_offset=int((streamwindowssizex - xsize)/2)
        y_offset=int((streamwindowssizey - ysize)/2)
        base[y_offset:y_offset+arrbase.shape[0], x_offset:x_offset+arrbase.shape[1]] = arrbase #center the image array
        cv2.imshow('Match', base)
        cv2.waitKey(1)  


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

   
def thresholdslider(value):

    global threshold
    threshold=int(value)/100
      

def about():
    
    top = Toplevel()
    top.wm_attributes("-topmost", 1)
    top.resizable(0, 0)
    top.focus()
    top.geometry("350x530")
    top.title('About')
    top.iconbitmap('favicon.ico')

    def copytoclpbrd():  
        pyperclip.copy(btcaddr)        
        msgf.configure(text='COPIED TO CLIPBOARD')

    def openweb():
        webbrowser.open_new('http://cockheromachine.blogspot.com')

    msg  = Message(top, width=300, text='COCK HERO MACHINE Ver.' + version)
    msga = Message(top, width=300, text='cockheromachine@gmail.com')
    msgb = Message(top, width=300, text='For more informations visit:')
    msgc = Button(top, height=1, width=40, text='cockheromachine.blogspot.com', command=openweb)#Message(top, width=300, text='cockheromachine.blogspot.com\n')
    msgd = Message(top, width=300, text='\nYou can support this project!')
    msge = Message(top, width=300, text='Bitcoin donations address:')
    msgf = Button(top, height=1, width=40, text=btcaddr, command=copytoclpbrd)
    

    msgg = Canvas(top, width=300, height=300, background='white')     
    resizeqr = cv2.resize(qrimage, (250, 250), interpolation = cv2.INTER_NEAREST)
    imagefromarray = Image.fromarray(resizeqr) 
    imagetk = ImageTk.PhotoImage(imagefromarray) 
    msgg.image=imagetk #to keep a reference else it shows blank
    msgg.create_image(152, 152, image=msgg.image)
    

                
    msg.pack()
    msga.pack()
    msgb.pack()
    msgc.pack()
    msgd.pack()
    msge.pack()
    msgf.pack()
    msgg.pack()

    button = Button(top, height=1, width=10, text="OK", command=top.destroy)
    button.pack()


def ontop():

    hwndmatch = win32gui.FindWindow(None,'Match')
    hwndstream = win32gui.FindWindow(None,'Stream')
    hwndconsole = win32console.GetConsoleWindow()

    if checkontopvar.get()==True:

        # windows on top:

        if hwndconsole != 0:

            rectconsole = win32gui.GetWindowRect(hwndconsole)
            win32gui.SetWindowPos(hwndconsole, win32con.HWND_TOPMOST, rectconsole[0], rectconsole[1], rectconsole[2]-rectconsole[0], rectconsole[3]-rectconsole[1], 0) 

        if hwndmatch != 0:
            recta = win32gui.GetWindowRect(hwndmatch)   # x = rect[0]   y = rect[1]    w = rect[2] - x    h = rect[3] - y
            win32gui.SetWindowPos(hwndmatch, win32con.HWND_TOPMOST, recta[0], recta[1], recta[2]-recta[0], recta[3]-recta[1], 0) 

        if hwndstream != 0:
            rectb = win32gui.GetWindowRect(hwndstream)
            win32gui.SetWindowPos(hwndstream, win32con.HWND_TOPMOST, rectb[0], rectb[1], rectb[2]-rectb[0], rectb[3]-rectb[1], 0) 

        root.wm_attributes("-topmost", 1) # root on top


    if checkontopvar.get()==False:       

        # windows NOT on top:

        if hwndconsole != 0:
            rectconsole = win32gui.GetWindowRect(hwndconsole)
            win32gui.SetWindowPos(hwndconsole, win32con.HWND_NOTOPMOST, rectconsole[0], rectconsole[1], rectconsole[2]-rectconsole[0], rectconsole[3]-rectconsole[1], 0) 

        if hwndmatch != 0:
            recta = win32gui.GetWindowRect(hwndmatch)   #  x = rect[0]   y = rect[1]    w = rect[2] - x    h = rect[3] - y
            win32gui.SetWindowPos(hwndmatch, win32con.HWND_NOTOPMOST, recta[0], recta[1], recta[2]-recta[0], recta[3]-recta[1], 0) 

        if hwndstream != 0:
            rectb = win32gui.GetWindowRect(hwndstream)
            win32gui.SetWindowPos(hwndstream, win32con.HWND_NOTOPMOST, rectb[0], rectb[1], rectb[2]-rectb[0], rectb[3]-rectb[1], 0) 

        root.wm_attributes("-topmost", 0) # root NOT on top


def on_entry_click(event):
    if comentry.get() == 'COM Port':
       comentry.delete(0, "end") # delete all the text in the entry
       comentry.insert(0, '') #Insert blank
       comentry.config(foreground = 'black')


def resetGUI():
    checkAO.deselect()
    checkPUL.deselect()
    checkDET.deselect()
    checkSET.deselect()
    slidera.config(foreground='gray')
    sliderb.config(foreground='gray', label='TIME ON(ms):')
    sliderc.config(foreground='gray')
    sliderd.config(foreground='gray')
    slidersizex.config(foreground='gray')
    slidersizey.config(foreground='gray')
    sliderthresh.config(foreground='gray')
    checkinvert.config(foreground='gray')
      
      
def inverttick():
    
    global checkinv
    checkinv=not checkinv


def patternmenu(value):

    global patternvar
    motor.stop()
    if '.srt' in value:
        srtselect(value) #read data from files
    
    patternvar=value
    
    alwaysONtick()
  


# TKINTER INTERFACE:  
  
root= Tk()
streamwindowssizex=220
streamwindowssizey=220

comtext = StringVar()
comentry=Entry(root, textvariable=comtext)
comentry.grid(row = 0, column = 0)
comentry.insert(0, "COM Port")
comentry.bind('<FocusIn>', on_entry_click)
comentry.config(fg = 'gray', width=13)

buttonserial=Button(root,height=1, width=8,text='CONNECT', command=lambda:serialstart(comtext.get(), serialbaud))
buttonserial.grid(row = 0, column = 1, sticky=W)

checkontopvar = BooleanVar()
checkontop=Checkbutton(root,text = 'On top', variable=checkontopvar, command=lambda:ontop())
checkontop.grid(row = 0, column = 3)
checkontop.select()

buttonabout=Button(root,height=1, width=8,text='About...', command=lambda:about())
buttonabout.grid(row = 0, column = 4)

namelist=[]
patternsetup('pattern.txt')#load patterns
srtsetup()#load srt files
patternvar='none'
pattern_variable = StringVar()
pattern_variable.set("PATTERNS")
optionmenu_widget = OptionMenu(root, pattern_variable, *namelist[1:], command=patternmenu)
optionmenu_widget.grid(row = 2, column=0)
optionmenu_widget.config(width=7)

checkAOVar = IntVar()
checkAO=Checkbutton(root,text = 'ON', command=lambda:alwaysONtick(), variable = checkAOVar)
checkAO.grid(row = 2, column = 1, pady=10)

checkPULVar = IntVar()
checkPUL=Checkbutton(root,text = 'PULSE', command=lambda:pulsetick(), variable = checkPULVar)
checkPUL.grid(row = 2, column = 2, pady=10)

checkDETVar = IntVar()
checkDET=Checkbutton(root,text = 'DETECT', command=lambda:detecttick(), variable = checkDETVar)
checkDET.grid(row = 2, column = 3, pady=10)

checkSETVar = IntVar()
checkSET=Checkbutton(root,text = 'DETECT SETUP', command=lambda:detectsetup(), variable = checkSETVar)
checkSET.grid(row = 2, column = 4, pady=10)

buttonpause=Button(root, height=2, width=60, text='-PAUSE/START-', command=lambda:motor.pause())
buttonpause.grid(row = 4, columnspan = 5, pady=10)

motorspeed=IntVar(value=10)
slidera = Scale(root, from_=0, to=255, orient=HORIZONTAL,length=400.00, variable=motorspeed, label='MOTOR SPEED:', command=speedslider)
slidera.grid(columnspan = 6,pady=5)
speed=(str(motorspeed.get()))

timeON=IntVar(value=200)
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
xsize=sizex.get()*(streamwindowssizex - 20)/100
    
sizey=IntVar(value=25)
slidersizey = Scale(root, from_=1, to=100, orient=HORIZONTAL,length=400.00, variable=sizey, label='Ysize:', command=slidersize)
slidersizey.grid(columnspan = 11,pady=5)
ysize=sizey.get()*(streamwindowssizey - 20)/100

thresh=IntVar(value=70)
sliderthresh = Scale(root, from_=1, to=100, orient=HORIZONTAL,length=400.00, variable=thresh, label='THRESHOLD:', command=thresholdslider)
sliderthresh.grid(columnspan = 12,pady=5)
threshold=int(thresh.get())/100

checkinv=False
checkinvert=Checkbutton(root,text = 'Invert', command=inverttick, variable=checkinv)
checkinvert.grid(columnspan = 13)


#THREADS:

arduino_connected=False
motor=motorclass()
tmotordetect=threading.Thread(target=motor.detect, args=())
tmotordetect.setDaemon(True)
tmotordetect.start()


#INITIALIZING:

pos=[-1,-1]
savelist=[] 
loadlist=[] 
shiftms=0
xsize=sizex.get()*(streamwindowssizex - 20)/100
ysize=sizey.get()*(streamwindowssizey - 20)/100
arrbase=np.zeros((streamwindowssizex, streamwindowssizey, 3), np.uint8) #an array of zeros for a black background
serialbaud=9600
arduino=None
keysetup('setup.txt') #assign keys from setup.txt
comportsetup() #list all available com ports
pygame.init()
hm = pyHook.HookManager() # hooking keyboard
hm.KeyDown = onKeyDown
hm.HookKeyboard() 
pygame.event.pump()
root.withdraw()
root.wm_attributes("-topmost", 1)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.title('CHM ' + version)
root.iconbitmap('favicon.ico')
root.deiconify()
resetGUI()
ontop()

##### bodged fix for 4k resolution and higher:
try:
    ctypes.windll.user32.SetProcessDPIAware()# Make the application DPI aware to accommodate 4K resolution
except:
    if debug==True:
        print('.SetProcessDPIAware() ERROR')

if GetSystemMetrics(0) < 3840 and GetSystemMetrics(1) < 2160: 
    root.resizable(1, 1)
    root.geometry("430x670")

else:
    root.resizable(1, 1)
    root.geometry("1024x1080")



qrimage = np.array([[[  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0]],

 [[255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255]],

 [[  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255]],

 [[  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255]],

 [[  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255]],

 [[255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0]],

 [[255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255]],

 [[  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255]],

 [[255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255]],

 [[  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255]],

 [[  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0]],

 [[255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255]],

 [[255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255]],

 [[  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255]],

 [[  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0]],

 [[255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255]],

 [[  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0]],

 [[  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [  0,   0,   0],
  [255, 255, 255],
  [  0,   0,   0],
  [255, 255, 255],
  [255, 255, 255],
  [  0,   0,   0]]], dtype=np.uint8)
btcaddr='34ajbSNuGKxz8jmN6xtU5RUDnVMynAPLf5'

root.mainloop()





    

    

