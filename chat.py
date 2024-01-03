from autogdb import *
import json
import os

from rich import print
from rich.progress import Progress

import warnings


warnings.filterwarnings("ignore", message="You are trying to use a chat model.*")
from rich import print

CACHE_FILE_PATH = '.server_cache.auotogpt.json'


lo = Logger()

def banner():
    banner = """\
    \n\n
           _____                _____)  ______    ______   
          (, /  |             /        (, /    ) (, /    ) 
            /---|     _/_ ___/   ___     /    /    /---(   
         ) /    |_(_(_(__(_)/     / )  _/___ /_ ) / ____)  
        (_/                (____ /   (_/___ /  (_/ ("""
    
    author = """\
        [bold red]>[/bold red] Author [bold blue]Retr0Reg[/bold blue], ChatWithBinary Team.       
    """
    print(banner)
    print(author)
    print('\n\n')

def check_for_keys():
    try:
        from api_key import OPENAI_API_KEY, OPENAI_API_BASE
        lo.success("API Key and API Base found!!!!")
    except ImportError:
        lo.fail("API key and base URL not found.")
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

def setup():
    USER_OPENAI_API_KEY, USER_OPENAI_API_BASE = check_for_keys()
    ip, port = get_server_info()
    pwnagent = PwnAgent(USER_OPENAI_API_KEY, USER_OPENAI_API_BASE, AutoGDB(server=ip, port=port).tool())
    chatagent = ChatAgent(USER_OPENAI_API_KEY, USER_OPENAI_API_BASE, pwnagent)
    return chatagent

def cli():
    chatagent = setup()
    while True:
        print(f"\n  [bold light_steel_blue1] Talk to [/bold light_steel_blue1][bold plum2]GDBAgent[/bold plum2]>>> ",end='')
        text_query = input()
        print(f"\n  [bold medium_purple1]:snowboarder: GDBAgent[/bold medium_purple1]: ", end='')
        chatagent.chat_and_assign(text_query)

if __name__ == "__main__":
    banner()
    cli()