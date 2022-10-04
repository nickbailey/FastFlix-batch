import os
import yaml
import argparse
import asyncio, asyncssh

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
mktmp_cmd = 'mktemp --tmpdir --directory FastFlix-attachments.XXXXXX'
# END OF SITE CUSTOMISATION

class sshSession :
    def __init__(self, conn : asyncssh.SSHClientConnection) :
        self.conn = conn
        
    async def cmd(self, cmd : str) -> (str, str, int) :
        result = await self.conn.run(cmd)
        return result.stdout, result. stderr, result.exit_status

async def main(host, **conn_args) :
    rs = sshSession(await asyncssh.connect(host, **conn_args))
    print(f"{(await rs.cmd('whoami'))[0]}@{(await rs.cmd('hostname'))[0]}")
    print(await rs.cmd('ls'))

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
        ## TODO should check this will always send the attachment
        ## which is the cover art path
        desc['cover'] = [ attachment['file_path']
                            for attachment in j['video_settings']['attachment_tracks'] ]
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
            print (f'{args.ssh_host}: {mktmp_cmd}')
            r_tmpdir, r_errs, r_rc = ('[tmp_dir]', '', 0)
        else :
            r_tmpdir, r_errs, r_rc = await rs.cmd(mktmp_cmd)
            r_tmpdir = r_tmpdir.rstrip()

    print(f"Created remote {r_tmpdir} with return code {r_rc}.\n", r_errs)

    # Upload cover art, replacing paths in job commands
    print ('Uploading cover graphics:')
    for j in jobs :
        for attachment in j['cover'] :
            print (f"\t{j['video_title']}... ")
            if args.dry_run :
                print (f"\tCopy: {attachment} -> {args.ssh_host}:{r_tmpdir}")
            else :
                await asyncssh.scp(attachment, (ssh_con, r_tmpdir))
            j['encode_command'] = j['encode_command'].replace(attachment, f"{r_tmpdir}/{os.path.basename(attachment)}")
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

if __name__ == '__main__' :
    import sys
    if len(sys.argv) == 2:
        asyncio.run(main(sys.argv[1]))
    else:
        print (f'No host specified. Will use {ssh_host_dflt}')

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

    asyncio.run(main())
