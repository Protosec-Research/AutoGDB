#encoding: utf-8
"""
@author: retr0@retr0.blog
"""

import base64
from langchain.agents import Tool
import httpx
import asyncio
from langchain.agents import initialize_agent
from langchain.chat_models.openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage
from . import pwndbg

import base64

def decode_bs64(encoded_text):
    base64_bytes = encoded_text.encode('utf-8')
    text_bytes = base64.b64decode(base64_bytes)
    return text_bytes.decode('utf-8')

def encode_bs64(text):
    text_bytes = text.encode('utf-8')
    base64_bytes = base64.b64encode(text_bytes)
    return base64_bytes.decode('utf-8')

class AutoGDB:

    def __init__(self,server: str,port: str) -> None:
        """
        This class is usually used to built the tool for PwnAgent to use,
        Please use GdbGpt().tool() to obtain the tool.
        """
        self.server = server
        self.port = port
        self.server_body = f"{self.server}:{self.port}"

    def await_autogdb_connecton(self):
        """
        Awaiting autoGDB connection
        """
        import requests
        session_without_proxies = requests.Session()
        session_without_proxies.trust_env = False
        endpoint_url = f"http://{self.server_body}/test-connection-cli/"
        try:
            response = session_without_proxies.get(endpoint_url)
            if response.status_code == 200:
                data = response.json()
                if data['message'] == 'success':
                    return {'message':'success',
                            'name':data['binary_name'],
                            'path':data['binary_path']
                            }
                else:
                    return {'message':'awaiting'}
            else:
                return {'message':'error','detail':response.status_code}
        except requests.exceptions.ConnectionError:
                pass
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

    async def gdb_send(self,command: str = None) -> str:
        """
        Sends a command to a local server and awaits the response.
        The command is sent as a query parameter 'instruction' to the '/instruct/' endpoint.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f'http://{self.server_body}/instruct/',
                params={'instruction': command},
                headers={'accept': 'application/json'}
            )
            response.raise_for_status() 
            return response.text
        
    def gdb_run(self,command: str = None) -> str:
        return asyncio.run(self.gdb_send(encode_bs64(str(command))))

    def tool(self) -> Tool:
        return Tool(
        name="gdb",
        func=self.gdb_run,
        description="Run gdb commands on this binary file on this specific frame in gdb, given arguments: command(only accept gdb in pwndbg version command)"
    )



class PwnAgent:
    
    def __init__(self,api_key: str,
                api_base: str, 
                autogdb: Tool, 
                binary_name='Unknown',
                binary_path='Unknown'
            ) -> None:
        

        self.autogdb = autogdb
        self.llm = ChatOpenAI(temperature=0.5,
            model_name='gpt-4-1106-preview',
            openai_api_base=api_base,
            openai_api_key=api_key,
            streaming=True,
            )
        
        self.template = f"""\
            You are a serious reverse-engineering helper who don't make reckless decision. You can use gdb\
            Current File name: {binary_name}, Path: {binary_path}
            A list of valid pwndbg commands: \n
            {pwndbg.base_prompt()} \n
            * Process-based analysis and dynamic analysis is recommanded.\
            * The program is already running
            * Keep using gdb if you want until you solve the problem throughly \
            * You can use commands like stack, rop, heap, that is built in pwndbg version of gdb\
            * When you use command \'run\', the user will help you Ctrl+C the program manuly.\\n\n
            * disassemble main are recommand starter for analysing\
            * When analysing the offset of stack overflows, pay attention to actual position of the variable on the stack\
            * use python3 and pyload look like run < <(python -c "print('A'*116 + 'B'*4 + 'C'*4)") to try to generate payloads\
            * When reporting a vulnerabilty, make sure to notice where the trigger, how can it be triggered?\
            * When you are ask to generate a payload for a vulnerabilty, you only need to return the basic structure of the pwntools exploition (b'a'*x+p64(address_of_return)...)
            """
        
        self.sysmessage = SystemMessage(content=self.template)

        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        self.agent = initialize_agent(
            agent="zero-shot-react-description",
            tools=[self.autogdb, pwndbg.read_command_docs],
            llm=self.llm,
            verbose=True,
            agent_kwargs={
                'system_message': self.template,
            }
        )

    def chat(self,input):
        return self.agent.run(self.template+input)

    
class ChatAgent:

    def __init__(self, api_key: str, api_base: str, pwnagent: PwnAgent) -> None:
        from langchain.agents import Tool
        from langchain.memory import ConversationBufferMemory
        from langchain.agents import initialize_agent
        from .streaming import FinalStreamingStdOutCallbackHandler

        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.llm = ChatOpenAI(
            temperature=0.5,
            model_name='gpt-4-1106-preview',
            openai_api_key=api_key,
            openai_api_base=api_base,
            streaming=True,
            callbacks=[FinalStreamingStdOutCallbackHandler()]
            )
        
        self.tool = Tool(
            name="GDB Agent",
            func=pwnagent.chat,
            description="Assign a job for your GDB Agent to do (For example: Find vulnerability in this binary)"
        )

        self.template = f"""\
            A list of valid pwndbg commands: \n
            {pwndbg.base_prompt()} \n
            You are a Reverse-engineering assistance call autoGDB, who have the ability call other assistance who have ability to use gdb.
            Your user may ask you to analysis some binary file, they meant the binary file that you \"Gdb assistance\" is dynamic-debugging.
            Your \"Gdb assistance\" have the ability to analysis and deduct the task you send and dynamic-debug it in gdb (with pwndbg installed) in vert-thought steps.
            Feel free to ask for you \"Gdb assistance\" and they will return the final answer to your task or problem to them
            Meanwhile, you are vert smart, you can find connections and do deduction with information you have.
            """
        
        self.sysmessage = SystemMessage(content=self.template)

        self.chat_conversation_agent = initialize_agent(
            agent="chat-conversational-react-description",
            tools=[self.tool, pwndbg.read_command_docs],
            llm=self.llm,
            verbose=False,
            max_iterations=3,
            memory=self.memory,
            agent_kwargs={
                'system_message': self.template,
            }
        )

    def chat_and_assign(self,input):
        return self.chat_conversation_agent.run(input)