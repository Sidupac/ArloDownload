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

This script is open-source; please use and distribute as you wish.
There are no warranties; please use at your own risk.
