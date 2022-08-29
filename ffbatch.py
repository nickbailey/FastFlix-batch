import os
import yaml
import argparse
import subprocess
import asyncio, asyncssh
from sshSession import sshSession

# SITE CUSTOMISATION
# Change the following if you don't like typing lots of
# command-line options.

# Path where exported filesystems are mounted on the client
mp_dflt = '/auto/hamlet/'

# Path of the exported filesystem appearing at the above mount point
export_dflt = '/export/'

# Default host on which to perform the encoding
ssh_host_dflt = 'hamlet'

# The command run on the server to make a temporary directory and
# return its name
mktmp_cmd = 'mktemp --tmpdir --directory FastFlix-covers.XXXXXX'
# END OF SITE CUSTOMISATION

# Use clp to parse the command line before anything else happens.
clp = argparse.ArgumentParser(
    description='Submit FastFlix commands as batch jobs.'
)
clp.add_argument('--mountpoint', type=str, default=mp_dflt,
                 help='''Path where the filesystem exported by the media server'
                         appears on the desktop client''')
clp.add_argument('--export', type=str, default=export_dflt,
                 help='''Path exported by the media server to the client''')
clp.add_argument('--list', action='store_true',
                 help='''List all jobs read before starting''')
clp.add_argument('--dry-run', action='store_true',
                 help='''Don't actually submit
                         jobs to the batch server's batch queue.
                         Print the job which would have been submitted
                         instead''')
clp.add_argument('--ssh-user', type=str,
		 help='''Login name of account on remote machine''')
clp.add_argument('--ssh-host', type=str, default=ssh_host_dflt,
		 help='''Remote host which will be running the encoding jobs''')
clp.add_argument('queue', type=str,
                 help='''YAML file containing the exported FastFlix job list''')

args = clp.parse_args()

async def main() -> None :

    # Read the whole of the named job queue from the yaml file.
    with open(args.queue, "r") as stream:
        q = yaml.safe_load(stream)

    # Extract video titles and encoding commands;
    # build a dictionary for each job.
    jobs = []
    for j in q['queue'] :
        desc = {}
        desc['video_title'] = j['video_settings']['video_title']
        desc['encode_command'] = ' && '.join([ 
            cc['command'] for cc in j['video_settings']['conversion_commands']
        ])
        ## TODO should check 0th attachment is the cover art path
        try :
            desc['cover'] = j['video_settings']['attachment_tracks'][0]['file_path']
        except :
            # Couldn't find cover attachment
            desc['cover'] = None
        jobs.append(desc)

    if args.list > 0:
        for j in jobs :
            print (f"\n{j['video_title']}\n==========================")
            print (f"{j['encode_command']}\n--------------------------")
            print (f"Cover: {j['cover']}\n==========================")

    # Start a remote session on the server
    sshargs = {}
    if args.ssh_user :
        sshargs['username'] = args.ssh_user
    
    ssh_con = await asyncssh.connect(args.ssh_host, **sshargs)
    rs = sshSession(ssh_con)

    # If there are any jobs to do, create a temp directory on the host to upload the cover art.
    if j :
        if args.dry_run :
            print (f'{args.ssh_host}; {mktmp_cmd}')
            r_tmpdir, r_errs, r_rc = ('[tmp_dir]', '', 0)
        else :
            r_tmpdir, r_errs, r_rc = await rs.cmd(mktmp_cmd)
            r_tmpdir = r_tmpdir.rstrip()

    print(r_tmpdir, r_errs, r_rc)

    # Upload cover art, replacing paths in job commands
    print ('Uploading cover graphics:')
    for j in jobs :
        if j['cover'] != None :
            print (f"\t{j['video_title']}... ")
            if args.dry_run :
                print (f"\tCopy: {j['cover']} -> {args.ssh_host}:{r_tmpdir}")
            else :
                await asyncssh.scp(j['cover'], (ssh_con, r_tmpdir))
            j['encode_command'] = j['encode_command'].replace(j['cover'], f"{r_tmpdir}/{os.path.basename(j['cover'])}")
    print ('Done')
    
    # Convert the encoding commands' paths to run on the server
    print ('Starting batch jobs:')
    for j in jobs :
        if j['encode_command'] :
            print (f"\t{j['video_title']}... ")
            j['encode_command'] = j['encode_command'].replace(args.mountpoint, args.export)
            batch_cmd = f"/usr/bin/batch << ENDOFCMD\n{j['encode_command']}\nENDOFCMD\n"
            if args.dry_run:
                print (f'\t{args.ssh_host}: {batch_cmd}')
            else :
                await rs.cmd(batch_cmd)
    print('Done')

asyncio.run(main())
