import cv2
import numpy as np
import pyscreenshot as ImageGrab
from tkinter import *
from Xlib import display
import mss
import os
import pyxhook
import serial
import threading
import serial.tools.list_ports
import ctypes
import glob
from PIL import ImageTk, Image
with open(os.devnull, 'w') as f: ###shutting up pygame silliness
    oldstdout = sys.stdout# disable stdout
    sys.stdout = f
    import pygame
    sys.stdout = oldstdout# enable stdout

version = '0.9.4l'
print('CHMACHINE Ver. %s \n' %version)



class motorclass():
    
    def __init__(self):
        self.state=2
        self.tempo=0
        self.savestate=2
        self.result=0 
        self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 4), np.uint8) #create an array of zeros for the black background
        self.index=0
        self.listindex=0
        self.timetic=0
        self.patternspeed=0
        self.speed='0'
        self.targetspeed='0'
        self.pinresttime=0
        self.serialfloodlimit=5 #time(ms) between commands to limit serial flooding
        

    def detect(self):
        
        global stream_window_open
        global stream_window
         

        while detectflag==True:          
            
            if arduino_connected==False:  

                pygame.time.wait(1)                                                        
           
            while ((self.state==5) or (self.state==1)): #################### DETECT/DETECT SETUP

                if self.state==5 and self.getspeed()!=0 and arduino_connected==True:

                    self.PWMpin('0')


                try: #take care of sliding too fast which result in a shape out of boundaries
                    self.monitor = {"top": top, "left": left, "width": int(screenshotsizex), "height": int(screenshotsizey)}
                    arr = np.array(mss.mss().grab(self.monitor))
                    self.result = cv2.matchTemplate(arr, arrbase, cv2.TM_CCOEFF_NORMED) #check if images match

                    if self.state==5:

                        if self.result>0:
                            print ('%.0f %% Match' %(self.result*100))
                        else:
                            print ('0 % Match')

                    
                    if checkinv==False: #invert flag False


                        if (self.result>=threshold): # if match value is over the threshold

                            if self.state==1 and arduino_connected==True: 
                                self.PWMpin(speed)
                            
                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 4), np.uint8) #create a black background
                            cv2.circle(self.colorshow,(0,0), 70, (0,255,0), -1) #draw a green circle 
                            self.tempo=pygame.time.get_ticks()
                    
                        elif (pygame.time.get_ticks()-self.tempo) >= (timeonvar):  #turn the pin to floor speed some time after the last match is occurred 

                            if self.state==1 and arduino_connected==True: 
                                self.PWMpin(floorspeed)
                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 4), np.uint8) #create a black background
                            

                    else: #invert flag True
                    
                        if (self.result<=threshold):#match if value is under the threshold

                            if self.state==1 and arduino_connected==True:
                                self.PWMpin(speed)

                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 4), np.uint8) #create a black background
                            cv2.circle(self.colorshow,(0,0), 70, (0,255,0), -1) #draw a green circle 
                            self.tempo=pygame.time.get_ticks()
                    
                        elif (pygame.time.get_ticks()-self.tempo) >= (timeonvar):  #turn the pin to floor speed some time after the last match is occurred 
                            
                            if self.state==1 and arduino_connected==True:
                                self.PWMpin(floorspeed)

                            self.colorshow=np.zeros((streamwindowssizex, streamwindowssizey, 4), np.uint8) #create a black background
                            

                    ###centering and overlapping images over background:
  
                    x_offset=int((streamwindowssizex - screenshotsizex)/2)
                    y_offset=int((streamwindowssizey - screenshotsizey)/2)
                    self.colorshow[y_offset:y_offset + arr.shape[0], x_offset:x_offset + arr.shape[1]] = arr 
                    
                    ###  
                
                except:
                    pass
                
                    
                if stream_window_open==False: # open "stream" window if isn't already opened
                                                        
                    stream_window= Toplevel()
                    stream_window.resizable(False,False)
                    stream_window.title('Stream')
                    stream_window.geometry(str(streamwindowssizex) + 'x' + str(streamwindowssizey))   
                    stream_window.protocol("WM_DELETE_WINDOW", on_closing_stream_window) 
                    stream_canvas = Canvas(stream_window, width=streamwindowssizex, height=streamwindowssizey, background='black')
                    stream_canvas.pack()
                    stream_window_open=True
                    
                    try:
    
                        iconpath=os.path.abspath(os.path.dirname(__file__)) + '/icon.gif'
                        imgicon = PhotoImage(file=iconpath)
                        stream_window.tk.call('wm', 'iconphoto', stream_window._w, imgicon)  
                    
                    except: 
                        pass
                    
                    ontop()
                

                else:
                    ###showing image:
                    self.im = cv2.cvtColor(self.colorshow, cv2.COLOR_BGRA2RGB)
                    self.imag = Image.fromarray(self.im)
                    self.imagi = ImageTk.PhotoImage(image=self.imag) 
                    stream_canvas.create_image(streamwindowssizex/2, streamwindowssizex/2, image=self.imagi)
                    stream_canvas.image=self.imagi #to keep a reference else it shows blank
                
                
                if self.state==1 and arduino_connected==True:
                    self.PWMpin(str(self.getspeed())) #Keeps the PWM pin alive(see Arduino code)
                    ###
                   
                pygame.time.wait(1)


            
            while self.state==2 and arduino_connected==True:#################### STOP/PAUSE
                
                self.PWMpin('0')
                pygame.time.wait(1)


            while self.state==3 and arduino_connected==True: ##################### ALWAYSON/PATTERN

                if patternvar=='none':

                    self.PWMpin(speed)
                    pygame.time.wait(1)
                
                else:
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

            if (pygame.time.get_ticks()-self.pinresttime) > self.serialfloodlimit: #limit serial flooding

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
       
        if self.state!=2:
            self.savestate=self.state
            self.state=2
            

        elif self.state==2:
            self.state=self.savestate
        

    def startdetect(self):
        self.state=1
        self.savestate=self.state

    def alwayson_pattern(self):
        
        self.state=3
        self.savestate=self.state

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

    linelist=[]

    ###default keys:
    pausebutton='P_Insert'
    slowdownbutton='P_End'
    speedupbutton='P_Down'
    screenshotbutton='F9'
    refreshbutton='F10'
    savebutton='F11'
    loadbutton='F12'
    ###

    try:

        
        setup  = open(file, 'r')

        for x in range(100):
            linelist=setup.readline().replace(' ', '').strip().split('=') #read line, remove spaces and split the string a the "=" sign

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
             
            if linelist[0] == 'Loadstate':
                loadbutton=linelist[1]

            if linelist[0] == 'Savestate':
                savebutton=linelist[1]


        setup.close() 
    except:
        print('Cannot open', file, ', loading default keys...\n')

    print('- HOTKEYS:\n')
    print('Pause -------------- ',pausebutton)
    print('Slow down ---------- ',slowdownbutton)
    print('Speed up ----------- ',speedupbutton)
    print('Screenshot --------- ',screenshotbutton)
    print('Screenshot update -- ',refreshbutton)
    print('Save state --------- ',savebutton)
    print('Load state --------- ',loadbutton)
    print('')
    print('') 

        
def patternsetup(file):

    global namelist
    global patternlist

    linelist=[]
    namelist=[]
    patternlist=[]
    namelist.append('PATTERN')
    namelist.append('none')
    patternlist.append([0])
    patternlist.append([0])
    try:
        patterntxt = open(file, 'r')    

        for x in range(1000):
            linelist=patterntxt.readline()        

            if linelist.strip()== '***':  #strip() removes spaces and end of line characters
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
            
            pass
        
        try:            

            print (p[0] + '...')
            arduino = serial.Serial(p[0], baud, timeout = 1, write_timeout = 1) # always a good idea to specify a timeout in case we send bad data
            pygame.time.wait(2000)# wait for Arduino to initialize

            arduino.write(('T').encode('utf-8'))
            pygame.time.wait(150)# wait for a response from Arduino
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
     
    
    if COMstring == ('') or COMstring == ('COM Port'): #if no port is specified start autoserialstart() to find it automatically
        tserial=threading.Thread(target=autoserialstart, args={serialbaud})
        tserial.setDaemon(True)
        tserial.start()

    
        
    #manual port:
    else:

        print (COMstring + ' - Initializing...')
        resetGUI()
        arduino_connected=False   
        motor.stop()   
                 
        try:
            if arduino.is_open:
                arduino.close()
                pygame.time.wait(500)            
        except:
            pass

        try:
            arduino = serial.Serial(COMstring, baud, timeout = 1, write_timeout = 1) # 2=Com3 on windows always a good idea to specify a timeout in case we send bad data
            pygame.time.wait(2000)# wait for the Arduino to initialize
            
            #test the connection(see Arduino code):
            arduino.write(('T').encode('utf-8'))
            pygame.time.wait(150)
            line = arduino.read(arduino.inWaiting()).decode(encoding='UTF-8',errors='replace')   
            if line.find('connOK')!=-1:
                print("CHM CONNECTED!")
                print (COMstring + ' - Initialization Complete.')
                arduino_connected=True
             
            else:
                print ('Wrong serial connection.')
                arduino.close()

        except serial.SerialTimeoutException:
            
            print (COMstring + ' TIMEOUT EXCEPTION. Try another port.')
            arduino.close()
            arduino_connected=False
                
        except:
            
            print('No port found.')

     
def onKeyDown(event):

    global speed
    global pos
    global arrbase
    global savelist
    global loadlist
    global top
    global left
    global screenshotsizex
    global screenshotsizey
    global match_window_open
    global match_window
    global match_canvas
    
# never put any condition before event.key 
    if event.Key == ('Return'):
        
        if comentry==root.focus_get() and comentry.get()!=(''):
            serialstart(comtext.get(), serialbaud)
       
    
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

            mousedata=display.Display().screen().root.query_pointer()._data
            pos=[mousedata['root_x'], mousedata['root_y']]
                    
        if (pos != [-1,-1]):
                        		
            print('Mouse position',pos)
            
            ###find black border width:
            screenshotsizex=sizex.get()*(streamwindowssizex - 20)/100
            screenshotsizey=sizey.get()*(streamwindowssizey - 20)/100
            ###
            
            top=int((pos[1]-screenshotsizey/2))
            left=int((pos[0]-screenshotsizex/2))
            
            ###adjusting screenshot position so it stays into screen boundaries:  
                  
            if left<0:
                
                left=0
            
            if top<0:
                
                top=0

                            
            if left + screenshotsizex > screenwidth:
                
                left=int(screenwidth-screenshotsizex)
                
            if top + screenshotsizey > screenheight:
                
                top=int(screenheight-screenshotsizey)
            
            ###
                
            monitor = {"top": top, "left": left, "width": int(screenshotsizex), "height": int(screenshotsizey)}
            arrbase = np.array(mss.mss().grab(monitor))       
            base=np.zeros((streamwindowssizex, streamwindowssizey, 4), np.uint8) #an array of zeros for a black background
            x_offset=int((streamwindowssizex-screenshotsizex)/2)
            y_offset=int((streamwindowssizey-screenshotsizey)/2)
            base[y_offset:y_offset+arrbase.shape[0], x_offset:x_offset+arrbase.shape[1]] = arrbase #center the image array         
    
            if match_window_open==False:# open "match" window if isn't already opened
                
                match_window= Toplevel()
                match_window.resizable(False,False)
                match_window.title('Match')
                match_window.geometry(str(streamwindowssizex) + 'x' + str(streamwindowssizey))   
                match_window.protocol("WM_DELETE_WINDOW", on_closing_match_window)
                match_canvas = Canvas(match_window, width=streamwindowssizex, height=streamwindowssizey, background='black')
                match_canvas.pack()    
                
                try:
    
                    iconpath=os.path.abspath(os.path.dirname(__file__)) + '/icon.gif'
                    imgicon = PhotoImage(file=iconpath)
                    match_window.tk.call('wm', 'iconphoto', match_window._w, imgicon)  
                
                except: 
                    pass
                                
                ontop()
                match_window_open=True 
                
            ###show image:
            
            im = cv2.cvtColor(base, cv2.COLOR_BGRA2RGB)
            imag = Image.fromarray(im)
            imagi = ImageTk.PhotoImage(image=imag) 
            match_canvas.image=imagi #to keep a reference in scope else it shows blank
            match_canvas.create_image(streamwindowssizex/2, streamwindowssizex/2, image=match_canvas.image)
                
            ###
                     

   
    if event.Key == (savebutton):

        filesname=glob.glob(os.path.abspath(os.path.dirname(__file__)) + "/*.npz") #find name of all .npz files in the main folder
        savelist=[]

        
        for x in filesname:
            
            try: #in case of a miswritten file name
                x = x[-9:-4]
                x=x.strip('save')                
                num=int(x) 
                savelist.append(num)
            except:
                pass

        if savelist!=[]:
            savename=(os.path.abspath(os.path.dirname(__file__)) + '/save' + str(max(savelist) + 1) + '.npz') #find the max value to add to the string
            
        else:
            savename=(os.path.abspath(os.path.dirname(__file__)) + '/save0.npz')

        np.savez(savename, arrbase, pos, int(screenshotsizex), int(screenshotsizey), speed, floorspeed, timeonvar, timeoffvar, threshold, checkinv)
        print(savename, 'SAVED')
        loadlist=[]

 

    if event.Key == (loadbutton):

        filesname=glob.glob(os.path.abspath(os.path.dirname(__file__)) + "/*.npz") #find name of all npz files in the main folder
        if loadlist==[]: 

            for x in filesname:
                try: #in case of a miswritten file name
                    x = x[-9:-4]
                    x=x.strip('save')
                    num=int(x) 
                    loadlist.append(num)
                except:
                    pass
                
        loadlist.sort() #sort numbers in the list

        if loadlist!=[]: 

            loadname=(os.path.abspath(os.path.dirname(__file__)) + '/save' + str(loadlist.pop()) + '.npz') # pop() removes last element and return it
            loaded_arrays = np.load(loadname)

            load_state(loaded_arrays['arr_0'], loaded_arrays['arr_1'], loaded_arrays['arr_2'], loaded_arrays['arr_3'], loaded_arrays['arr_4'],
                       loaded_arrays['arr_5'], loaded_arrays['arr_6'], loaded_arrays['arr_7'], loaded_arrays['arr_8'], loaded_arrays['arr_9'])
            print(loadname, 'LOADED')
        else:
            print('nothing to load')
              
        
    return True


def load_state(image_arrayl, posl, xsizel, ysizel, speedl, floorspeedl, timeonvarl, timeoffvarl, thresholdl, checkinvl):
    
    global screenshotsizex
    global screenshotsizey
    global speed
    global timeonvar
    global timeoffvar
    global floorspeed
    global threshold
    global arrbase
    global arr
    global pos
    global top
    global left
    global checkinv
    global match_window_open
    global match_window
    global match_canvas

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
    
    ###
    

    ###load and display image:

    if posl[0] != -1:

        pos = [posl[0], posl[1]]
        top=int((posl[1]-screenshotsizey/2))
        left=int((posl[0]-screenshotsizex/2))
        arrbase=image_arrayl
        arr=image_arrayl
        sizex.set(xsizel/2)
        sizey.set(ysizel/2)
        screenshotsizex=(xsizel/2)*(streamwindowssizex - 20)/100
        screenshotsizey=(ysizel/2)*(streamwindowssizey - 20)/100
        x_offset=int((streamwindowssizex - screenshotsizex)/2)
        y_offset=int((streamwindowssizey - screenshotsizey)/2)
        base=np.zeros((streamwindowssizex, streamwindowssizey, 4), np.uint8) #an array of zeros for a black background
        base[y_offset:y_offset+arrbase.shape[0], x_offset:x_offset+arrbase.shape[1]] = arrbase #center the image array   
        
        if match_window_open==False:# open "match" window if isn't already opened
                
                match_window= Toplevel()
                match_window.resizable(False,False)
                match_window.title('Match')
                match_window.geometry(str(streamwindowssizex) + 'x' + str(streamwindowssizey))   
                match_window.protocol("WM_DELETE_WINDOW", on_closing_match_window)
                match_canvas = Canvas(match_window, width=streamwindowssizex, height=streamwindowssizey, background='black')
                match_canvas.pack()    
                
                try:
    
                    iconpath=os.path.abspath(os.path.dirname(__file__)) + '/icon.gif'
                    imgicon = PhotoImage(file=iconpath)
                    match_window.tk.call('wm', 'iconphoto', match_window._w, imgicon)  
                
                except: 
                    pass
                                
                ontop()
                match_window_open=True 
             
        im = cv2.cvtColor(base, cv2.COLOR_BGRA2RGB)
        imag = Image.fromarray(im)
        imagi = ImageTk.PhotoImage(image=imag) 
        match_canvas.image=imagi #to keep a reference else it shows blank
        match_canvas.create_image(streamwindowssizex/2, streamwindowssizex/2, image=match_canvas.image)
        
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
                        slidera.config(foreground='black')
                        sliderb.config(foreground='black', label='PATTERN FREQ:')
                        sliderd.config(foreground='black')
                        checkAO.select()
                        motor.alwayson_pattern()

            else:
                print('No serial connection')
                checkAO.deselect()
        except:
            print('No serial connection')
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


def on_closing_match_window():
    
    global match_window_open
    global match_window
    
    match_window_open=False
    match_window.destroy()
    
def on_closing_stream_window():
    
    global stream_window_open
    global stream_window
    
    stream_window_open=False
    stream_window.destroy()

def on_closing():
    
    global detectflag
    motor.stop()
    detectflag=False 
    print ('Bye Bye')
    pygame.time.wait(1)
    hm.cancel()
    cv2.destroyAllWindows()
    root.quit()
    root.destroy() 
    print ('Be vigilant')
    sys.exit()



def slidersize(value):
    
    global arrbase
    global screenshotsizex
    global screenshotsizey
    global top
    global left

    screenshotsizex=sizex.get()*(streamwindowssizex - 20)/100
    screenshotsizey=sizey.get()*(streamwindowssizey - 20)/100
 
    if pos != [-1,-1]:
        
        top=int((pos[1]-screenshotsizey/2))
        left=int((pos[0]-screenshotsizex/2))
        
     ### adjusting screenshot position so it stays into screen boundaries:  
                  
        if left<0:
            
            left=0
        
        if top<0:
            
            top=0

                        
        if left + screenshotsizex > screenwidth:
            
            left=int(screenwidth-screenshotsizex)
            
        if top + screenshotsizey > screenheight:
            
            top=int(screenheight-screenshotsizey)
            
    ###
        
    
    ### show image:
        monitor = {"top": top, "left": left, "width": int(screenshotsizex), "height": int(screenshotsizey)}
        arrbase = np.array(mss.mss().grab(monitor))
        base=np.zeros((streamwindowssizex, streamwindowssizey, 4), np.uint8) #an array of zeros for a black background
        x_offset=int((streamwindowssizex-screenshotsizex)/2)
        y_offset=int((streamwindowssizey-screenshotsizey)/2)
        base[y_offset:y_offset+arrbase.shape[0], x_offset:x_offset+arrbase.shape[1]] = arrbase #center the image array
         
        im = cv2.cvtColor(base, cv2.COLOR_BGRA2RGB)
        imag = Image.fromarray(im)
        imagi = ImageTk.PhotoImage(image=imag) 
        
        try: # if the window is not opened an exception occur
            
            match_canvas.image=imagi #to keep a reference else it shows blank
            match_canvas.create_image(streamwindowssizex/2, streamwindowssizex/2, image=match_canvas.image)
            
        except:
            pass
    ###

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
    top.resizable(False,False)
    top.focus()
    top.geometry("220x150")
    top.title('About')
    try:

        iconpath=os.path.abspath(os.path.dirname(__file__)) + '/icon.gif'
        imgicon = PhotoImage(file=iconpath)
        top.tk.call('wm', 'iconphoto', top._w, imgicon)  
                    
    except: 
        pass

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


def ontop():
	

     if checkontopvar.get()==True:
         
         root.wm_attributes("-topmost", 1) #  on top
         
         try:#if the window is not opened an exception occur
             match_window.wm_attributes("-topmost", 1)# on top 
         except:
             pass
             
         try:
             stream_window.wm_attributes("-topmost", 1)# on top 
         except:
             pass

     if checkontopvar.get()==False:
         
         root.wm_attributes("-topmost", 0) #  NOT on top
         
         try:
             match_window.wm_attributes("-topmost", 0)# NOT on top 
         except:
             pass
              
         try:
             stream_window.wm_attributes("-topmost", 0)# NOT on top 
         except:
             pass


def on_entry_click(event):
    if comentry.get() == 'COM Port':
       comentry.delete(0, "end") # delete all the text in the entry widget
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

patternsetup(os.path.abspath(os.path.dirname(__file__)) + '/pattern.txt')#load patterns
patternvar='none'
pattern_variable = StringVar()
pattern_variable.set("PATTERNS")
optionmenu_widget = OptionMenu(root, pattern_variable, *namelist[1:], command=patternmenu)
optionmenu_widget.grid(row = 2, column=0)
optionmenu_widget.config(width=7)

checkAOVar = IntVar()
checkAO=Checkbutton(root,text = 'ALWAYS ON', command=lambda:alwaysONtick(), variable = checkAOVar)
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
screenshotsizex=sizex.get()*(streamwindowssizex - 20)/100
    
sizey=IntVar(value=25)
slidersizey = Scale(root, from_=1, to=100, orient=HORIZONTAL,length=400.00, variable=sizey, label='Ysize:', command=slidersize)
slidersizey.grid(columnspan = 11,pady=5)
screenshotsizey=sizey.get()*(streamwindowssizey - 20)/100

thresh=IntVar(value=70)
sliderthresh = Scale(root, from_=1, to=100, orient=HORIZONTAL,length=400.00, variable=thresh, label='THRESHOLD:', command=thresholdslider)
sliderthresh.grid(columnspan = 12,pady=5)
threshold=int(thresh.get())/100

checkinv=False
checkinvert=Checkbutton(root,text = 'Invert', command=inverttick, variable=checkinv)
checkinvert.grid(columnspan = 13)


#THREADS:

detectflag=True
arduino_connected=False
motor=motorclass()
tmotordetect=threading.Thread(target=motor.detect, args=())
tmotordetect.setDaemon(True)
tmotordetect.start()


#INITIALIZING:

pos=[-1,-1]
top=0
left=0
savelist=[] 
loadlist=[] 
screenshotsizex=sizex.get()*(streamwindowssizex - 20)/100
screenshotsizey=sizey.get()*(streamwindowssizey - 20)/100
serialbaud=9600
arduino=None
keysetup(os.path.abspath(os.path.dirname(__file__)) + '/setup.txt') #assign keys from setup.txt
comportsetup() #list all available com ports
pygame.init()
hm = pyxhook.HookManager() # hooking keyboard
hm.KeyDown = onKeyDown
hm.HookKeyboard() 
hm.start()
pygame.event.pump()
root.withdraw()
root.wm_attributes("-topmost", 1)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.title('CHM ' + version)
root.resizable(False,False)

try:
    
    iconpath=os.path.abspath(os.path.dirname(__file__)) + '/icon.gif'
    imgicon = PhotoImage(file=iconpath)
    root.tk.call('wm', 'iconphoto', root._w, imgicon)  

except: 
    pass
    
screenwidth, screenheight = root.winfo_screenwidth(), root.winfo_screenheight()# get the screen resolution
match_window_open=False
stream_window_open=False
root.deiconify()
resetGUI()
ontop()
root.mainloop()
