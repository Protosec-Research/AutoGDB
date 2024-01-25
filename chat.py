from autogdb import *
import json
import os

from rich import print
from rich.progress import Progress
import readline


import warnings


warnings.filterwarnings("ignore", message="You are trying to use a chat model.*")
from rich import print

CACHE_FILE_PATH = '.server_cache.autogdb.json'


lo = Logger()

def clear_screen():
    import platform
    if platform.system() == "Windows":
        subprocess.run("cls", shell=True)
    else:
        subprocess.run("clear", shell=True)

def banner():
    banner = """\
    \n\n
           _____                _____)  ______    ______   
          (, /  |             /        (, /    ) (, /    ) 
            /---|     _/_ ___/   ___     /    /    /---(   
         ) /    |_(_(_(__(_)/     / )  _/___ /_ ) / ____)  
        (_/                (____ /   (_/___ /  (_/ ("""
    
    author = """\n\
        Enable GPT in your reversing job.
        [bold red]>[/bold red] Author [bold blue]Retr0Reg[/bold blue], ChatWithBinary Team.       
    """
    clear_screen()
    print(banner,end='')
    print(author,end='')
    print('\n')

def check_for_keys():
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", default="https://api.openai.com/v1")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    lo.success("Loaded API key and base URL from environment.")

    try:
        from api_key import OPENAI_API_KEY, OPENAI_API_BASE
    except:
        if not OPENAI_API_KEY or not OPENAI_API_BASE:
            lo.fail("API key or base URL not found.")
            OPENAI_API_KEY = input("Please enter your OpenAI API key: ").strip()
            OPENAI_API_BASE = input("Please enter the OpenAI API base URL: ").strip()

            with open('api_key.py', 'w') as file:
                file.write(f'OPENAI_API_KEY = "{OPENAI_API_KEY}"\n')
                file.write(f'OPENAI_API_BASE = "{OPENAI_API_BASE}"\n')

            lo.success("api_key.py file created with your API key and base URL.")

            # Re-import after creating the file
            from api_key import OPENAI_API_KEY, OPENAI_API_BASE

    return OPENAI_API_KEY, OPENAI_API_BASE

def console_input(input_str: str) -> str:
    print(input_str, end='')
    return input()

def get_server_info():
    if os.path.exists(CACHE_FILE_PATH):
        with open(CACHE_FILE_PATH, 'r') as cache_file:
            try:
                server_info = json.load(cache_file)
                addr = server_info['ip']
                port = server_info['port']
                
                if (not addr) or (not port):
                    raise KeyError(f"Server address and port saved is empty, please save it again by deleting:{CACHE_FILE_PATH}")
                
                return addr,port
                
            except json.JSONDecodeError:
                lo.fail("Cache file is corrupted. Please enter server details again.")

    # Cache file doesn't exist or is corrupted, ask the user for info
    server_ip = console_input("[bold light_steel_blue1][?] Please enter your server IP:[/bold light_steel_blue1] ").strip()
    server_port = console_input("[bold light_steel_blue1][?] Please enter your server port:[/bold light_steel_blue1] ").strip()
    try:
        with open(CACHE_FILE_PATH, 'w') as cache_file:
            json.dump({'ip': server_ip, 'port': server_port}, cache_file)
        lo.success(f"Server address and port saved, change it by deleting {CACHE_FILE_PATH}.")
    except Exception as e:
        lo.fail("Save address and port failed, please check for your privilege and etc.")

    return server_ip, server_port

import subprocess
import socket
import signal
import os

class AutoGDBServer:
    def __init__(self,url,port) -> None:
        self.url = url
        self.port = port
        self.proc = None

    
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
            lo.success(f"AutoGDB server started at {self.url}:{self.port}")
            lo.info(f"You can use: autogdb {self.url} {self.port}")
            self.proc = subprocess.Popen(["uvicorn", "main:app", "--host", str(self.url), "--port", str(self.port), "--reload"],
                                        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                        cwd="server/"
                                    )

        except Exception as e:
            lo.fail(str(e))
    
    def exit(self):
        os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)

def setup():
    USER_OPENAI_API_KEY, USER_OPENAI_API_BASE = check_for_keys()
    ip, port = get_server_info()
    autogdb_server = AutoGDBServer(ip,port)
    autogdb_server.start_uvicorn()
    pwnagent = PwnAgent(USER_OPENAI_API_KEY, USER_OPENAI_API_BASE, AutoGDB(server=ip, port=port).tool())
    chatagent = ChatAgent(USER_OPENAI_API_KEY, USER_OPENAI_API_BASE, pwnagent)
    return chatagent, autogdb_server

def cli():
    chatagent, autogdb_server = setup()
    try:
        while True:
            text_query = console_input(f"\n  [bold light_steel_blue1] Talk to [/bold light_steel_blue1][bold plum2]GDBAgent[/bold plum2]>>> ")
            print(f"  [bold medium_purple1]:snowboarder: GDBAgent[/bold medium_purple1]: ", end='')
            chatagent.chat_and_assign(text_query)
    
    except KeyboardInterrupt:
        lo.info("Bye!",PrevReturn=True)

    except Exception as e:
        lo.fail(e)

    finally:
        autogdb_server.exit()

if __name__ == "__main__":
    banner()
    cli()