# FastFlix-batch

ffbatch is a small python program which executes the encode jobs
described in a YAML queue file saved from the excellent [Fastflix](https://github.com/cdgriffith/FastFlix)
program by [Chris Griffith](https://github.com/cdgriffith) and '[leonardyan](https://github.com/leonardyan)'.
It is released under GPL version 3 without warranty in the hope that it might be useful
to others. See the file LICENCE.txt for details (yes, LICEN**C**E, because it's a noun).

## Use Case

You've mastered your 4k UHD masterpiece on your desktop machine, "ophelia".
You want to compress the media for distribution to your chums, so you fire
up FastFlix and create a job to do that. You could do the work on your desktop
machine but it is a big deal, using kilowatts of power: it's going to take
a while and use lots of RAM while you would prefer to get on with something else.
You have a headless media server called "hamlet" which can run the ffmpeg commands
needed to perform the compression, albeit not very fast. So instead of hitting
FastFlix's *start* button, you save the encode queue to a file and run this
program on it. Hamlet's CPU fan starts up, keeping the room nice and warm,
and you can just forget about the whole process until you get an email with
the completion report.

## Implementation

The YAML file saved by FastFlix contains the ffmpeg commands to run, so most of the work
is already done. Only the following needs to be fixed up:
 * The files saved on ophelia in a directory served by hamlet won't appear in the
 same place when accessed on hamlet. For example ``hamlet:/export/video/The_life_of_Rosser.mkv``
 be ``/mnt/The_life_of_Rosser.mkv`` on ophelia. To make things right, you'd need to
 specify ``--mountpoint=/mnt/ --export=/export/video/`` on the command line (or
 edit the *site customisation* section at the top of ``ffbatch.py``)
 * If you've put a cover picture in your video file, FastFlix is going to extract
 it prior to encoding and place it in a system-dependent place with a unique (and long) name.
 If any such files are referenced in the job list, a temporary directory
 will be created on hamlet, and all such files copied to it. The encode commands
 will of course be adjusted to refer to these files.
 * Each job will be set running using the ``batch`` command. This means they will only
 start when hamlet hasn't much better to do.
 
 ## Requirements
 
 Installation commands are for debian Linux.
 
 * Python 3 on ophelia. You should have it already.
 * Python 3's `asyncssh` on ophelia `apt install python3-asyncssh` will install it.
 * The `batch` command on hamlet. `apt install at` will install it.
 * An account on hamlet with the same username as the one on ophelia, configured
 so that ssh can log in without passswords.
 
 ## Usage
 
 Usage details are printed when the ``-h`` flag is passed.
 ```
nick@ariel:~/Packages/FastFlix-batch$ python3 ffbatch.py -h
usage: ffbatch.py [-h] [--mountpoint MOUNTPOINT] [--export EXPORT] [--list] [--dry-run]
                  [--ssh-user SSH_USER] [--ssh-host SSH_HOST]
                  queue

Submit FastFlix commands as batch jobs.

positional arguments:
  queue                 YAML file containing the exported FastFlix job list

optional arguments:
  -h, --help            show this help message and exit
  --mountpoint MOUNTPOINT
                        Path where the filesystem exported by the media server' appears on the desktop
                        client
  --export EXPORT       Path exported by the media server to the client
  --list                List all jobs read before starting
  --dry-run             Don't actually submit jobs to the batch server's batch queue. Print the job which
                        would have been submitted instead
  --ssh-user SSH_USER   Login name of account on remote machine
  --ssh-host SSH_HOST   Remote host which will be running the encoding jobs
```
 ### Finding out what's in the queue.
 
 Start up a terminal session on hamlet and type ``atq`` (or, if you have loads of queues,
 ``atq -q b``. By default ``batch`` jobs go in the ``b`` queue). For example:
 
 ```
nick@hamlet:~$ atq
27      Sun Aug 28 20:57:00 2022 b nick
25      Sun Aug 28 20:57:00 2022 = nick
26      Sun Aug 28 20:57:00 2022 b nick
```
 shows two waiting batch (``b``) jobs and a running job. To see what the running job is,
 first note that it's number 25, then type ``at -c 25``.
 
 ### Tidying up
 
 ``ffbatch`` doesn't (deliberately) delete anything. You'll maybe want to delete
 the directory ``/tmp/FastFlix-covers*`` after all batch jobs complete, which will
 have copies of the cover graphics in it, now included in the encoded files. They
 typically aren't very big, so if you don't bother, that's fine. They'll disappear
 at the next reboot.
