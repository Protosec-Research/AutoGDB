from autogdb import *
from .models import *

from rich.progress import Progress, SpinnerColumn, Progress
from rich import print

from dotenv import load_dotenv
import argparse
import warnings
import json
import os
import time


warnings.filterwarnings("ignore", message="You are trying to use a chat model.*")
lo = Logger()

def console_input(input_str: str,pure_input=True) -> str:
    print(input_str, end='')
    input_text = input('\033[0m')
    if not pure_input:
        input_text = input(' >>> \033[0m')
    return input_text

def get_server_info():
    CACHE_FILE_PATH = '.server_cache.autogdb.json'
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
                lo.fail("Cache file is corrupted. Please enter server details again.", exit_flag=False)

    # Cache file doesn't exist or is corrupted, ask the user for info
    server_ip = console_input("    [bold slate_blue1][?] Please enter your [italic medium_purple1]server address[/italic medium_purple1]:[/bold slate_blue1] ").strip()
    server_port = console_input("    [bold slate_blue1][?] Please enter your [italic medium_purple1]server port[/italic medium_purple1]:[/bold slate_blue1] ").strip()
    
    try:
        with open(CACHE_FILE_PATH, 'w') as cache_file:
            json.dump({'ip': server_ip, 'port': server_port}, cache_file)
        lo.success(f"Server address and port saved, change it by deleting {CACHE_FILE_PATH}.")

    except Exception as e:
        lo.fail("Save address and port failed, please check for your privilege and etc.")

    print('\n')
    return server_ip, server_port

def check_for_keys():
    load_dotenv(verbose=True)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", default="https://api.openai.com/v1")
    lo.success("Loaded API key and base URL from environment.")

    if not OPENAI_API_BASE or not OPENAI_API_KEY:
        # lo.info("API key or base URL not found.")
        OPENAI_API_KEY = console_input("    [bold slate_blue1][?] Please enter your [italic medium_purple1]OpenAI API key[/italic medium_purple1]:[/bold slate_blue1] ").strip()
        OPENAI_API_BASE = console_input("    [bold slate_blue1][?] Please enter the [italic medium_purple1]OpenAI API base URL[/italic medium_purple1]:[/bold slate_blue1] ").strip()

        with open('.env', 'w') as file:
            file.write(f'OPENAI_API_KEY={OPENAI_API_KEY}\n')
            file.write(f'OPENAI_API_BASE={OPENAI_API_BASE}\n')

    return OPENAI_API_KEY,OPENAI_API_BASE

def parsing():

    parser = argparse.ArgumentParser(
        prog='AutoGDB',
        description='Enable GPT in your reversing job with GDB.',
    )
    parser.add_argument('--serverless',help='Run AutoGDB without bulit-in server',dest='serverless', action='store_true')
    parser.add_argument('--clue',help='Possible provided clues or helpful description of this challenge?', dest='clue')
    parser.add_argument('--clean-history',help='Clear previous commandline history of AutoGDB.', action='store_true')
    return parser.parse_args()

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
    return banner+author+'\n'


def await_until_connection(autogdb: AutoGDB):
    lo.info("Waiting AutoGDB to connect....")

    with Progress("   ", # Prev padding                                           
                  SpinnerColumn(),                           
                  "[progress.description]{task.description}",
                  transient=True) as progress:

        task = progress.add_task("[bold medium_purple2]Waiting for connecting...[/bold medium_purple2]", total=None)
        while True:
            try:
                frame = autogdb.await_autogdb_connecton()
                if frame['message'] == 'success':
                    time.sleep(0.1)
                    lo.success(f"Recieved connection from:",PrevReturn=True)
                    print(f"[bold medium_purple1]    Binary Name: {frame['name']}\n    Binary Path: {frame['path']}[/bold medium_purple1]")
                    return frame['name'],frame['path']
                
                elif frame['message'] == 'awaiting':
                    pass

                elif frame['message'] == 'error':
                    lo.fail(f"Error recieved from AutoGDB connection: {frame['detail']}")

                else:
                    lo.fail(f"Unknown respone from AutoGDB connection: {frame}")

            except Exception as e:
                pass


            time.sleep(5)
            progress.update(task, advance=0.1)

def setup(args):

    USER_OPENAI_API_KEY, USER_OPENAI_API_BASE   = check_for_keys()
    ip, port                                    = get_server_info()
    args                                        = parsing()

    history_manager                             = CliHistory()
    autogdb                                     = AutoGDB(server=ip, port=port)
    autogdb_server                              = AutoGDBServer(ip,port,logger=lo)


    history_manager.load_history()
    if args.clean_history:
        history_manager.clear_history()
        lo.info("History cleaned!\n")
        exit()

    if args.serverless:
        name=''
        path=''
    else:
        autogdb_server.start_uvicorn()
        name,path = await_until_connection(autogdb=autogdb)


    if args.clue:
        pwnagent = PwnAgent(USER_OPENAI_API_KEY, USER_OPENAI_API_BASE,
                             autogdb.tool(),
                             binary_name=name,
                             binary_path=path,
                             clue=args.clue)
    else:
        pwnagent = PwnAgent(USER_OPENAI_API_KEY, USER_OPENAI_API_BASE,
                             autogdb.tool(),
                             binary_name=name,
                             binary_path=path)

    chatagent = ChatAgent(USER_OPENAI_API_KEY,USER_OPENAI_API_BASE,pwnagent)

    return chatagent, autogdb_server, history_manager

def main(chatagent, history_manager):
    text_query = console_input(f"\n  [bold light_steel_blue1] Talk to [/bold light_steel_blue1][bold plum2]GDBAgent[/bold plum2]",pure_input=False)
    print(f"  [bold medium_purple1]:snowboarder: GDBAgent[/bold medium_purple1]: ", end='')

    chatagent.chat_and_assign(text_query)
    history_manager.save_history()


def cli():
    args = parsing()
    autogdb_server, history_manager = None, None
    try:
        banner()
        chatagent, autogdb_server, history_manager = setup(args=args)
        while True:
            main(chatagent,history_manager)
    
    except KeyboardInterrupt:

        lo.info("Bye!",PrevReturn=True)
        history_manager.save_history()

    except Exception as e:

        lo.fail(e)

    finally:
        if not args.serverless and autogdb_server:
            autogdb_server.exit()