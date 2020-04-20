ArloDownload for WINDOWS

Automatically download new video recordings from Arlo to local folders or Dropbox.  (Dropbox function not tested on Windows)
Optionally concatenate videos that are close in time. If the concat fails then the original video will still be downloaded

Additionally, there is now an autorun batch script that allows you to schedule a task and record a log of events

Video files are backed up under the following pathname:

      <rootdir>/<camera>/YYYY-MM-DD/HH:MM:SS+<duration>s.mp4

where

      rootdir       Name of the downloaded data directory, as configured, or Dropbox app folder
      YYYY-MM       Month the video was created
      YYYY-MM-DD    Date the video was created
      camera        Name of the camera, as configured in config
      HH:MM:SS      Time (24hr) the video was created
      duration      Total duration of the video, in seconds



Originally developped by Tobias Himstedt <himstedt@gmail.com>
Updated by Preston Lee <zettaiyukai@gmail.com>, Janick Bergeron <janick@bergeron.com>

Modified and adapted for Windows by James (Sid) Reynolds <Sidupac@gmail.com>

How to install:
      1. Download ffmpeg.exe and place the file within the install folder. 
            (Alternatively copy it directly to  c:\windows\. This allows the script to call the ffmpeg function to concat videos)
      2. Download and install python-3.8.2-amd64.exe  (https://www.python.org/ftp/python/3.8.2/python-3.8.2-amd64.exe)
            a. Select to Install on PATH > Custom Install > next > Install for All Users
      3. run the install.bat file as admin - this installs the modules and copies ffmpeg.
            Alternatively run the following commands manually:
            python -m pip install dropbox
            python -m pip install psutil
            python -m pip install requests
      4. set up the config file
      5. optionally: create a scheduled task to run autorun.bat

This script is open-source; please use and distribute as you wish.
There are no warranties; please use at your own risk.
