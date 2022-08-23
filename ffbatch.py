import yaml
import argparse

# Path where exported filesystems are mounted on the client
mp_dflt = '/auto/hamlet'

# Path of the exported filesystem appearing at the above mount point
export_dflt = '/export'

# Use clp to parse the command line
clp = argparse.ArgumentParser(
    description='Submit FastFlix commands as batch jobs.'
)
clp.add_argument('--mountpoint', type=str, default=mp_dflt,
                 help='''Path where the filesystem exported by the media server'
                         appears on the desktop client''')
clp.add_argument('--export', type=str, default = export_dflt,
                 help='''Path exported by the media server to the client''')
clp.add_argument('--list', action='store_true',
                 help='''List all jobs read before starting''')
clp.add_argument('queue', type=str,
                 help='''YAML file containing the exported FastFlix job list''')

args = clp.parse_args()

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


if args.list:
    for j in jobs :
        print (f"{j['video_title']}\n==========================\n{j['encode_command']}\n--------------------------\nCover: {j['cover']}\n==========================\n")
