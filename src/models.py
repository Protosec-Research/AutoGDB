from rich import print
import subprocess
import socket
import signal
import os


class AutoGDBServer:
    def __init__(self,url,port,logger) -> None:
        self.url = url
        self.port = port
        self.proc = None
        self.lo = logger

    
    def check_port(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.connect((self.url, int(self.port)))
                return False
            except socket.error:
                return True

    def start_uvicorn(self):
        try:
            if not self.check_port():
                raise Exception(f"The port {self.port} for autogdb server is used/busy, please change your port")
            self.lo.success(f"AutoGDB server started at {self.url}:{self.port}")
            self.lo.info(f"You can use: ",end='')
            print(f"[bold green]autogdb {self.url} {self.port}[/bold green]")
            self.proc = subprocess.Popen(["uvicorn", "main:app", "--host", str(self.url), "--port", str(self.port), "--reload"],
                                        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                        cwd="server/"
                                    )

        except Exception as e:
            self.lo.fail(str(e))
    
    def exit(self):
        os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)