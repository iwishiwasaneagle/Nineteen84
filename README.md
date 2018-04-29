# Nineteen84 - A surveillance system for my room

This spaghetti code sends an e-mail to me with pictures if motion is detected in my room. It also uploads 3 minutes worth of photos (3s intervals, not video because my RPi couldn't handle my crap webcam) to google drive. 

Interfacing is done with a switch and 3 leds - green, amber and red. When the system is off (i.e. switch is off) the green LED is solid, if it's active and on cooldown the amber is solid and the green flashes, if the system is primed then the amber is solid, and if it's been triggered the amber is solid and the red flashes. 

To use google drive, the pydrive library was used which has some weird command line authentication but so far I only had to do this on the first run. Since then it's cached the credentials in "mycreds.ini" file (obviously not uploaded). It also required an app to be registered with google and those details are saved in "client_secret.json". For email, the email library that comes with python was utilized and my credentials stored in "keys.py". 

## //TODO
- Create config file integration (hard coded right now yikes...)
