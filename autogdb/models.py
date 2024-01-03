#encoding: utf-8
"""
@author: retr0@retr0.blog
"""

from langchain.agents import Tool
import httpx
import asyncio
from langchain.agents import initialize_agent
from langchain.chat_models.openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

class AutoGDB:

    def __init__(self,server: str,port: str) -> None:
        """
        This class is usually used to built the tool for PwnAgent to use,
        Please use GdbGpt().tool() to obtain the tool.
        """
        self.server = server
        self.port = port
        self.server_body = f"{self.server}:{self.port}"

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
        return asyncio.run(self.gdb_send(str(command)))

    def tool(self) -> Tool:
        return Tool(
        name="gdb",
        func=self.gdb_run,
        description="Run gdb commands on this binary file on this specific frame in gdb, given arguments: command(only accept gdb in pwndbg version command)"
    )



class PwnAgent:
    
    def __init__(self,api_key: str,api_base: str,autogdb: Tool) -> None:
        self.autogdb = autogdb
        self.llm = ChatOpenAI(temperature=0.5,
            model_name='gpt-4-1106-preview',
            openai_api_base=api_base,
            openai_api_key=api_key,
            streaming=True,
            )
        
        self.prompt = PromptTemplate(
            input_variables=[],
            template="""\
            You are a serious CTF player who don't make reckless decision. You can use gdb\
            * When Users ask about a binary, they meant the binary inside the gdb. \
            * Use \'continue\', but never use \'run\' \
            * When doing analysis on a binary, make sure to make judgement base on code, for example, only based on checksec isn't acceptable. \
            * When reporting a vulnerability, make sure to report Where is the vuln; payload to exploit this vulnerability. \
            * You are inside of gdb (in pwndbg version) \
            * Keep using gdb if you want until you solve the problem throughly \
            * The file is currently loaded, and paused in a certain frame\
            * You can use commands like stack, heap, that is built in pwndbg version of gdb\
            * When you use command \'run\', the user will help you Ctrl+C the program manuly.\
            """
        )

        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        self.agent = initialize_agent(
            agent="zero-shot-react-description",
            tools=[self.autogdb],
            llm=self.llm,
            verbose=True,
        )

    def chat(self,input):
        return self.agent.run(input)

    
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

        self.chat_conversation_agent = initialize_agent(
            agent="chat-conversational-react-description",
            tools=[self.tool],
            llm=self.llm,
            verbose=False,
            max_iterations=3,
            memory=self.memory
        )

    def chat_and_assign(self,input):
        return self.chat_conversation_agent.run(input)