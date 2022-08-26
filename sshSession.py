import asyncio, asyncssh

class sshSession :
    def __init__(self, conn : asyncssh.SSHClientConnection) :
        self.conn = conn
        
    async def cmd(self, cmd : str) -> (str, str, int) :
        result = await self.conn.run(cmd)
        return result.stdout, result. stderr, result.exit_status

async def main(host) :
    rs = sshSession(await asyncssh.connect(host))
    print(f"{(await rs.cmd('whoami'))[0]}@{(await rs.cmd('hostname'))[0]}")
    print(await rs.cmd('ls'))

if __name__ == '__main__' :
    import sys
    if len(sys.argv) == 2:
        asyncio.run(main(sys.argv[1]))
    else:
        print ('Need a host!')
