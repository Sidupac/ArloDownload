#
# ArloDownload - A video backup utility for the Netgear Arlo System
# THIS DOESN'T WORK WITH 2FA ENABLED!
#
#
# Version 3.1w  > converted to windows
#
# Contributors:
#  Janick Bergeron <janick@bergeron.com>
#  Preston Lee <zettaiyukai@gmail.com>
#  Tobias Himstedt <himstedt@gmail.com>

# Edited and converted to Windows by:
#  James (Sidupac) Reynolds <sidupac@gmail.com> April 2020


#https://www.python.org/ftp/python/3.8.2/python-3.8.2-amd64.exe
# Select to Install on PATH > Custom Install > next > Install for All Users
# Then run install.bat to get additional modules, and install ffmpeg
# # install.bat contents:
# # @echo off
# # @setlocal enableextensions
# # @cd /d "%~dp0"
# # cls
# # python -m pip install dropbox
# # python -m pip install psutil
# # python -m pip install requests
# # copy /y "%~dp0\ffmpeg.exe" "C:\windows\ffmpeg.exe"
# # pause

import argparse
import configparser
import datetime
import dropbox
import json
import os
import pickle
import psutil
import requests
import signal
import shutil
import sys
import time

# Timestamp for this run
today = datetime.date.today()

# Parse command-line options
parser = argparse.ArgumentParser()
# Make the debug mode default to avoid clobberring a running install
parser.add_argument('-X', action='store_const', const=0, dest='debug', default=0, help='debug mode')
parser.add_argument('-i', action='store_const', const=1, dest='init',  default=0, help='Initialize the pickle file')
args = parser.parse_args()

config = configparser.ConfigParser()
config.read(os.path.dirname(os.path.abspath(__file__))+'\\arlo.conf')

rootdir = config['Default']['rootdir']
alreadydownloaded = config['verbose']['alreadydownloaded']

# In debug mode, do not interfere with the regular data files
if args.debug:
    rootdir = rootdir + ".debug"
if not os.path.exists(rootdir):
    os.makedirs(rootdir)

# Check if another instance is already running
lock = os.path.join(rootdir, "ArloDownload.pid")
if os.path.isfile(lock):
    pid = int(open(lock, 'r').read())
    if pid == 0:
        print(lock + " file exists but connot be read. Assuming an instance is already running. Exiting.")
        sys.exit
        
    if psutil.pid_exists(pid):
        # if the lock file is more than a few hours old, we got ourselves something hung...
        if ((time.time() - os.path.getmtime(lock)) < 60*60*6):
            print("An instance is already running. Exiting.")
            sys.exit()
        print("Process " + str(pid) + " appears stuck. Killing it.")
        os.kill(pid, signal.SIGTERM);
        sleep(1)
        if psutil.pid_exists(pid):
            print("ERROR: Unable to kill hung process. Exiting.")
            sys.exit()
        # We can proceed and claim this run as our own...


# I guess something crashed. Let's go ahead and claim this run!
open(lock, 'w').write(str(os.getpid()))


# Load the files we have already backed up
dbname = os.path.join(rootdir, "saved.db")
saved = {}
if os.path.isfile(dbname):
    try:
        saved = pickle.load(open(dbname, "rb"))
    except:
        # File was corrupted. Worst that is going to happen is we'll re-fetch everything.
        # Oh well...
        pass

    
class dropboxBackend:
    def __init__(self):
        self.backend = dropbox.Dropbox(config['dropbox.com']['token'])
        print("Dropbox login!")

    def backup(self, fromStream, todir, tofile):
        path = os.path.join(todir, tofile)
        print("Dropboxing " + path)
        self.backend.files_upload(fromStream.read(), "/" + path)

        
class localBackend:
    def __init__(self):
        self.rootdir = rootdir

    def backup(self, fromStream, todir, tofile):
        path = os.path.join(self.rootdir, todir)
        if not os.path.exists(path):
            os.makedirs(path)
        path = os.path.join(path, tofile)
        if not os.path.exists(path):
            print("Downloading " + path)
            with open(path, 'wb') as out_file:
                shutil.copyfileobj(fromStream, out_file)
        
    
class arlo_helper:
    def __init__(self):
        # Define your Arlo credentials.
        self.loginData = {"email":config['my.arlo.com']['userid'], "password":config['my.arlo.com']['password']}
        # Cleanup switch; this must be set to "True" in order to use the cleaner module.
        self.enableCleanup = False
        # All directories in format YYYYMMDD, e.g. 20150715, will be removed after x days.
        self.cleanIfOlderThan = 60
        # Define camera common names by serial number.
        self.cameras = {}
        self.concatgap = {}
        self.deleteAfterDays = {}
        for cameraNum in range (1, 10):
            sectionName = "Camera.{}".format(cameraNum)
            if sectionName in config:
                self.cameras[config[sectionName]['serial']] = config[sectionName]['name']
                if 'concatgap' in config[sectionName]:
                    self.concatgap[config[sectionName]['serial']] = int(config[sectionName]['concatgap'])
                if 'keep' in config[sectionName]:
                    self.deleteAfterDays[config[sectionName]['serial']] = int(config[sectionName]['keep'])
                else:
                    self.deleteAfterDays[config[sectionName]['serial']] = 99
        # Which backend to use?
        if not args.debug and 'dropbox.com' in config and 'token' in config['dropbox.com']:
            self.backend = dropboxBackend()
        else:
            self.backend = localBackend()
        self.localSave = localBackend()
                
        # No customization of the following should be needed.
        self.loginUrl = "https://my.arlo.com/hmsweb/login"
        self.deviceUrl = "https://my.arlo.com/hmsweb/users/devices"
        self.metadataUrl = "https://my.arlo.com/hmsweb/users/library/metadata"
        self.libraryUrl = "https://my.arlo.com/hmsweb/users/library"
        self.headers = {'Content-type': 'application/json', 'Accept': 'text/plain, application/json'}
        self.session = requests.Session()

    # Return the tiemstamp, in seconds, of an Arlo video item
    def getTimestampInSecs(self, item):
        return int(int(item['name']) / 1000)

    # Return the output directory name corresponding to an Arlo video item
    def getOutputDir(self, item):
        camera = str(self.cameras[item['deviceId']])
        month  = str(datetime.datetime.fromtimestamp(self.getTimestampInSecs(item)).strftime('%Y-%m'))
        date   = str(datetime.datetime.fromtimestamp(self.getTimestampInSecs(item)).strftime('%Y-%m-%d'))
        #return os.path.join(month, date, camera)
        return os.path.join(camera, date)

    # Return the output file name corresponding to an Arlo video item
    def getOutputFile(self, item):
        time = str(datetime.datetime.fromtimestamp(self.getTimestampInSecs(item)).strftime('%H.%M.%S'))
        secs = item['mediaDurationSecond']
        return time + "+" + str(secs) + "s.mp4"

    # Return the unique tag corresponding to an Arlo video item
    def getTag(self, item):
        camera = item['deviceId']
        return camera + item['name']

    
    def login(self):
        response = self.session.post(self.loginUrl, data=json.dumps(self.loginData), headers=self.headers )
        jsonResponseData = response.json()['data']
        

        if (jsonResponseData.get('error')):
            print("Error connecting to Arlo, received response was:")
            print("  "+jsonResponseData['reason'])
            raise SystemExit(0)
        else:
            print("Arlo login!")
            self.token = jsonResponseData['token']
            self.deviceID = jsonResponseData['serialNumber']
            self.userID = jsonResponseData['userId']
            self.headers['Authorization'] = self.token

    def readLibrary(self):
        now = today.strftime("%Y%m%d")
        # A 7-day window ought to be enough to catch everything!
        then = (today - datetime.timedelta(days=7)).strftime("%Y%m%d")
        params = {"dateFrom":then, "dateTo":now}
        response = self.session.post(self.libraryUrl, data=json.dumps(params), headers=self.headers)
        
        self.library = response.json()['data']
        # Separate the videos in their different cameras
        self.cameraLibs = {}
        for item in self.library:
            if item['deviceId'] in self.cameras:
                if item['deviceId'] not in self.cameraLibs:
                    self.cameraLibs[item['deviceId']] = []
                self.cameraLibs[item['deviceId']].append(item)

    def processLibrary(self, library, deleteAfterDays):
        deleteBefore = (today - datetime.date.fromtimestamp(0)).total_seconds() - (deleteAfterDays * 24 * 60 * 60)
        deleteItems = []
        
        itemCount = 0
        nItems = len(library)
        lastConcat = 0
        conresult=0
        for idx, item in enumerate(library):
            url = item['presignedContentUrl']
            todir = self.getOutputDir(item)
            tofile = self.getOutputFile(item)
            
            # Did we already process this item?
            tag = self.getTag(item)
            if args.init:
                saved[tag] = today

            if not args.debug and tag in saved:
                if alreadydownloaded != 0 and alreadydownloaded != "0":
                    print("We already have processed " +  todir + "\\" + tofile + "! Skipping download.")

                # If the video is too old, add it to the list to delete
                # (this way, we'll only delete videos we have previously saved)
                if self.getTimestampInSecs(item) < deleteBefore:
                    print("Will delete " +  todir + "\\" + tofile + " from my.arlo.com.")
                    deleteItems.append(item)

            else:

                # Should it be concatenated with the next video?
                # Note: library is ordered in reverse time order (newer first)
                if idx > lastConcat and item['deviceId'] in self.concatgap:
                    startIdx = idx
                    lastSec  = self.getTimestampInSecs(item)
                    # Find out how far back we can go with the maximum concatenation gap between videos
                    while (startIdx < nItems-1):
                        startIdx = startIdx + 1
                        prevSec = self.getTimestampInSecs(library[startIdx])
                        gap = lastSec - prevSec - int(library[startIdx]['mediaDurationSecond'])
                        if (gap > self.concatgap[item['deviceId']]):
                            break
                        
                        lastSec = prevSec

                    # If we found more than one video...
                    if startIdx-1 > idx:
                        conresult=self.concatenate(library[idx:startIdx])
                        lastConcat = startIdx - 1

                if idx > lastConcat or conresult ==0 :
                    # Save the video unless it was saved as part of the concatenation
                    itemCount = itemCount + 1
                    response = self.session.get(url, stream=True)
                    self.backend.backup(response.raw, todir, tofile)
                    del response
                #else:
                    #print("###  debug:  Skipping Download of concat: " + tofile)

                saved[tag] = today
                    
            if itemCount % 25 == 0:
                # Take a snapshot of what we have done so far, in case the script crashes...
                pickle.dump(saved, open(dbname, "wb"))

        if deleteItems:
            response = self.session.post(self.libraryUrl + "/recycle",
                                         json={'data':deleteItems},
                                         headers=self.headers)


    def concatenate(self, videos):
        # Clean up the concatenation working directory...
        dirname = "ffmpeg.work";
        workdir = os.path.join(rootdir, dirname);
        if (os.path.exists(workdir)):
            shutil.rmtree(workdir)
        os.makedirs(workdir)

        print("Concatenating videos:")
        flist = []
        # Get the videos to concatenate locally
        for item in reversed(videos):
            url = item['presignedContentUrl']
            filename  = item['name']+".mp4"
            print("    " + os.path.join(self.getOutputDir(item), self.getOutputFile(item)))
            response = self.session.get(url, stream=True)
            self.localSave.backup(response.raw, dirname, filename)

            flist.append(filename)

        # How long does the concatenated video cover?
        # Remember, videos are in reverse order (most recent first)
        totalSecs = self.getTimestampInSecs(videos[0]) - self.getTimestampInSecs(videos[-1]) + int(videos[0]['mediaDurationSecond'])
        time = str(datetime.datetime.fromtimestamp(self.getTimestampInSecs(videos[-1])).strftime('%H.%M.%S'))
        outfile = time + "+" + str(totalSecs) + "s.mp4"

        # If concatenation fails, oh well....
        try:
            # First, convert the MP4 into something that can be concatenated
            for mp4 in (flist):
                if os.path.exists(workdir+"\\"+mp4):
                    os.system("echo file '"+workdir+"\\"+mp4+"'"+">>\""+workdir+"\list.txt\"")

            # Concatenate using ffmpeg...
            os.system("ffmpeg -safe 0 -f concat -i \""+workdir+"\list.txt\" -c copy \""+workdir+"\concat.mp4\"")

            # And finally, upload!
            f = open(workdir+"\\concat.mp4", "rb")
            self.backend.backup(f, self.getOutputDir(videos[-1]), outfile)
            f.close()
            return 1
        except:
            print("Something went wrong during concatenation... downloading the original segments")
            return 0
            
    def cleanup(self):
        # Remove the entries in the "saved" DB for files that are no longer available on the arlo server
        for tag in saved:
            if saved[tag] != today:
                del saved[tag]
                
        if not self.enableCleanup:
            return
        older = today - datetime.timedelta(days = self.cleanIfOlderThan)
        directoryToCheck = older.strftime("%Y%m%d")
        removeDir = os.path.join(self.downloadRoot,directoryToCheck)
        print("Removing " + removeDir)
        if os.path.exists(removeDir):
            shutil.rmtree(removeDir)

thisHelper = arlo_helper()
thisHelper.login()
thisHelper.readLibrary()
for camera, videos in thisHelper.cameraLibs.items():
    thisHelper.processLibrary(videos, thisHelper.deleteAfterDays[camera])

# Save everything we have done so far...
pickle.dump(saved, open(dbname, "wb"))

#tidy up..
dirname = "ffmpeg.work";
workdir = os.path.join(rootdir, dirname);
if (os.path.exists(workdir)):
    shutil.rmtree(workdir)
            
            
print('Done!')

os.unlink(lock)
