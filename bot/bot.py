#!/usr/bin/env python3
import sys,os,asyncio
ep=os.path.join(os.path.dirname(__file__),"..",".env.docker.secret")
if os.path.exists(ep):
    with open(ep) as f:
        for ln in f:
            if "=" in ln and not ln.strip().startswith("#"):
                kv=ln.strip().split("=",1); os.environ[kv[0]]=kv[1]
from handlers.commands import handle_start,handle_help,handle_health,handle_labs,handle_scores
CMDS={"/start":handle_start,"/help":handle_help,"/health":handle_health,"/labs":handle_labs,"/scores":handle_scores}
async def run(cmd):
    p=cmd.strip().split(); cn,ar=p[0],p[1:] if len(p)>1 else None
    if cn not in CMDS: return "Unknown command. Use /help to see available commands."
    return await CMDS[cn](ar)
def main():
    if "--test" in sys.argv:
        i=sys.argv.index("--test")
        if i+1<len(sys.argv): print(asyncio.run(run(sys.argv[i+1]))); return
    print("LMS Bot running. Use --test <command> to test.")
if __name__=="__main__": main()
