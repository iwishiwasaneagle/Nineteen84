from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import logging, time, os

class drive:
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
        logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)
        logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

        self.logger.debug('Drive module imported. Beginning auth')
        self.gauth = GoogleAuth()

        #GDrive location for folders for pics
        self.DrivePicLocation = "SurveillancePics"

    def auth(self):
        #Load credentials
        self.gauth.LoadCredentialsFile("mycreds.ini")
        if self.gauth.credentials is None: #If there are no creds
            self.gauth.CommandLineAuth()
            self.logger.info("Command line authentication")
        elif self.gauth.access_token_expired: #If token has expired
            self.gauth.Refresh()
            self.logger.info("Token refreshed")
        else:
            self.gauth.Authorize() #Other wise do this
            self.logger.info("Authorization succesful")
        self.gauth.SaveCredentialsFile("mycreds.ini")

    def folder_check(self, name, parent, drive): #Checks if the folder of name exists under parent. If not it creates the folder
        found = False

        folder_list = drive.ListFile({'q': "'%s' in parents and trashed=false"%parent}).GetList()

        for folder in folder_list:
            if folder['title'] == name:
                fid = folder['id']
                found = True
                self.logger.info('Folder %s found under id %s'%(name, fid))
        if found == False:
            folder_meta = {'title':name, 'mimeType':'application/vnd.google-apps.folder', "parents":[{'id':parent}]}
            folder = drive.CreateFile(folder_meta)
            folder.Upload()
            fid = folder['id']
            self.logger.info("Folder '%s' not found. Created under fid %s"%(name, fid))

        return fid

    def upload(self, files, fileLocation): #Upload a list of files to a folder
        self.auth()
        drive = GoogleDrive(self.gauth)
        t = time.strftime("%d%m%y_%H%M%S")

        rootid = self.folder_check(self.DrivePicLocation, 'root', drive)
        fid = self.folder_check(t, rootid, drive)

        for file_ in files:
            file_meta = {'title':str(file_), "parents":[{'id':fid}], }
            f1 = drive.CreateFile(file_meta)
            f1.SetContentFile(fileLocation+file_)
            f1.Upload()
            self.logger.info(file_+" uploaded")


if __name__=="__main__":
    t =time.time()
    d = drive()
    d.upload(['README.md'], os.getcwd()+"/")
    print "Time elapsed: "+str(round(time.time()-t,1))+"s"
