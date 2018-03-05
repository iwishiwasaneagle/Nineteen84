from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
import time, smtplib, logging



class mail:
    def __init__(self, fileLocation):
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

        try:
            import keys
        except Exception, e:
            logger.error('File keys.py not found')

        self.to_addr = keys.CLIENT_EMAIL
        self.from_addr = keys.SERVER_EMAIL
        self.passw = keys.SERVER_PASS

        self.files = []
        self.fileLocation = fileLocation
        self.location = "Bedroom"

    def send(self):
        self.logger.info('Starting sending protocol')
        time_ = str(time.strftime("%H:%M %d/%m/%y"))
        msg = MIMEMultipart()
        msg['From'] = self.from_addr
        msg['To'] = self.to_addr
        msg['Subject'] = "Motion detected at "+time_
        body = "There was motion detected in "+self.location+" at "+time_
        msg.attach(MIMEText(body, 'plain'))
        if len(self.files)>0:
            self.logger.info('Files found. Attaching to email.')
            for f in self.files:
                attachment = open(self.fileLocation+f, "rb")
                part = MIMEBase('application', 'octet-stream')
                part.set_payload((attachment).read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', "attachment; filename= %s" % f)
                msg.attach(part)
                self.logger.info("Email to "+self.to_addr+": attachment added "+f)

        self.logger.info('Beginning sending of email')
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(self.from_addr, self.passw)
        text = msg.as_string()
        server.sendmail(self.from_addr, self.to_addr, text)
        server.quit()
        self.logger.info("Email sent to "+self.to_addr)
