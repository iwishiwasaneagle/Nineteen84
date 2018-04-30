import sqlite3
import cv2 as cv
import numpy as np
import time, os, random, logging
import RPi.GPIO as GPIO
import mail #Own module

class Monitor:
    def __init__(self):
        #logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler("runtime.log")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        #ch = logging.StreamHandler()
        #ch.setLevel(logging.DEBUG)
        #ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        self.home = os.getcwd()
        self.logger.debug("Beginning setup")

        self.piclocation = self.home+"/pictures/"
        self.sentpictures = self.home+"/pictureArchive/"
        if not os.path.isdir(self.piclocation):
            os.makedirs(self.piclocation)
        if not os.path.isdir(self.sentpictures):
            os.makedirs(self.sentpictures)

        self.picBuff = []
        self.picBuffLen = 50
        self.emailPicBuffLen = 10
        self.cam = cv.VideoCapture(0)
        self.font = cv.FONT_HERSHEY_SIMPLEX
        self.modes = {"MotionFast":[1, 10], "MotionSlow":[4, (2*60)/4]}
        self.mode = 0
        self.CD = 3*60
        self.lastCall = time.time()+self.CD

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self.PIRPin = 21
        self.SwitchPin = 20
        self.LEDamber = 9
        self.LEDgreen = 26
        self.LEDredPin = 10
        self.LEDredPinFrequency = 1
        self.LEDgreenPinFrequency = 0.7
        GPIO.setup([self.PIRPin, self.SwitchPin], GPIO.IN)
        GPIO.setup([self.LEDgreen, self.LEDamber, self.LEDredPin], GPIO.OUT)
        GPIO.output(self.LEDgreen, GPIO.LOW)
        GPIO.output(self.LEDamber, GPIO.HIGH)
        self.LEDred = GPIO.PWM(self.LEDredPin,self.LEDredPinFrequency)
        self.LEDgreenPWM = GPIO.PWM(self.LEDgreen,self.LEDgreenPinFrequency)

        self.mail = mail.mail(self.piclocation)

        try:
            import drive
            self.drive = drive.drive()
            self.drive.auth()
            self.logger.debug("Drive imported and authenticated")
        except Exception, e:
            self.logger.error("Import of drive module failed.", exc_info=True)

        self.logger.debug("Setup completed")

    def pic(self):
        s, img = self.cam.read()
        c = 0
        while not s:
            time.sleep(0.05)
            s, img = self.cam.read()
            c+=1
            if c>5:
                self.logger.error("Cammera error. Resetting VideoCapture object.")
                self.cam = cv.VideoCapture(0)
                s, img = self.cam.read()
                break
        if s:
            picFileName = str(time.strftime("%d%m%y_%H%M%S"))
            if not os.path.isfile(self.piclocation+picFileName+".png"):
                picFileName+=".png"
            else:
                picFileName = picFileName+"_2"+".png"

            cv.putText(img,time.strftime("%d/%m/%y %H:%M:%S %Z"),(10,470), self.font, 1,(255,255,255),1)
            cv.imwrite(self.piclocation+picFileName, img)
            self.logger.debug("Picture taken and saved under name %s @ %s"%(picFileName, self.piclocation))
            self.picBuff.append(picFileName)

    def email(self, pics):
        self.mail.files = pics
        try:
            self.mail.send()
        except Exception, e:
            self.logger.error("Email failed to send.", exc_info=True)

    def archive(self, files, location, dest):
        for file_ in files:
            try:
                os.rename(location+file_, dest+file_)
                self.logger.info("Moving %s to %s from %s"%(file_, dest, location))
            except Exception, e:
                self.logger.error("File %s doesn't exist in %s"%(file_, location), exc_info=True)

    def driveUp(self, pic):
        try:
            self.drive.upload(pic, self.piclocation)
            self.logger.info("Pictures uploaded to drive succesfully")
        except Exception, e:
            self.logger.error("Upload of pictures to drive failed. Trying again.", exc_info=True)
            try:
                self.drive=drive.drive()
                self.drive.auth()
                self.drive.upload(pic, self.piclocation)
                self.logger.error("Pictures uploaded to drive succesfully on second attempt")
            except:
                self.logger.error("Second attempt failed.")

    def interrupt(self, pin):
        #print self.motion, self.lastCall, time.time(), (self.lastCall)<time.time(), (self.lastCall)-time.time()
        #self.logger.debug("Interrupt detected")
        if not self.motion and self.lastCall<time.time() and GPIO.input(self.SwitchPin)==1:
            self.logger.debug("Interrupt detected")
            GPIO.output(self.LEDgreen, GPIO.HIGH)
            self.picBuff = []
            self.motion = True
            self.LEDred.start(50)


    def main(self):
        counter = 0
        self.set_ = False
        self.motion = False
        GPIO.add_event_detect(self.PIRPin, GPIO.RISING, callback=self.interrupt, bouncetime=300)
        while True:


            if GPIO.input(self.SwitchPin)==1:

                GPIO.output(self.LEDamber, GPIO.HIGH)
                if self.motion == False and self.set_ == False:
                    self.LEDgreenPWM.start(50)
                    self.set_ = True
                if self.motion == True and self.set_ == True:
                    self.LEDgreenPWM.stop()
                    #GPIO.output(self.LEDgreen, GPIO.HIGH)

                if self.motion and self.lastCall<time.time():
                    self.LEDgreenPWM.stop()
                    t = time.time()

                    if counter<self.modes["MotionFast"][1]:
                        self.pic()
                        self.logger.debug("Fast: picture taken")
                        wait = self.modes["MotionFast"][0]
                    elif counter==self.modes["MotionFast"][1]:
                        self.email(self.picBuff)
                        self.logger.debug("Email sent")
                        wait = 0
                    elif counter<self.modes["MotionSlow"][1]:
                        self.pic()
                        self.logger.debug("Slow: picture taken")
                        wait = self.modes["MotionSlow"][0]
                    else:
                        self.logger.debug("Executing drive upload")
                        self.driveUp(self.picBuff)
                        self.logger.debug("Drive upload executed")
                        name = self.sentpictures+str(time.strftime("%d%m%y_%H%M"))+"/"
                        if not os.path.isdir(name):
                            self.logger.info("Folder %s created"%name)
                            os.makedirs(name)
                        self.archive(self.picBuff, self.piclocation, name)
                        self.motion=False
                        self.lastCall = time.time()+self.CD
                        wait = 0
                        counter = -1

                    if wait-(time.time()-t)<0:
                        wait = 0
                    else:
                        wait = wait-(time.time()-t)

                    counter += 1
                    time.sleep(wait)
                else:
                    #self.logger.debug("Time till CD is over: %ds %s"%(round(self.lastCall-time.time(), 2), self.motion))
                    time.sleep(5)
            else:
                GPIO.output(self.LEDgreen, GPIO.HIGH)
                GPIO.output(self.LEDamber, GPIO.LOW)
                self.LEDred.stop()
                self.lastCall = time.time()+self.CD
                self.set_ = False


    def __del__(self):
        try:
            GPIO.cleanup()
            self.logger.debug("GPIO cleaned up")
        except:
            pass

if __name__=="__main__":
    d = Monitor()
    d.main()
