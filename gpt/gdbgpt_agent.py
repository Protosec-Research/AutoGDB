#encoding: utf-8
"""
@author: retr0@retr0.blog
"""
# Import things that are needed generically

from langchain.agents import initialize_agent
from langchain.llms import OpenAI
from langchain import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

# import custom tools
from instruct_gdb import Gdbgpt



llm = OpenAI(temperature=0.5,
            model_name='gpt-4-1106-preview',
            openai_api_base="https://ai-yyds.com/v1",
            openai_api_key="sk-5tzrrbESxAWLDppg39B7DaF0F5B94b69A47e570d3e930804"
            streaming=True
            )

prompt = PromptTemplate(
    input_variables=[],
    template="""\
    You are a serious CTF player who don't make reckless decision. \
    * Use continue, but never use run \
    * You are inside of gdb (in pwndbg version) \
    * The file is currently loaded, and paused in a certain frame\
    * You can use commands like stack, heap, that is built in pwndbg version of gdb\
    * When you use command \'run\', the user will help you Ctrl+C the program manuly.\
    """
)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
llm_gdb_chain = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=True
)

tools = [Gdbgpt]


# Construct the react agent type.
# agent.run("Seek way to exploit this file, Generate the final payload")
# agent = initialize_agent(
#     tools,
#     llm,
#     agent="zero-shot-react-description",
#     verbose=True
# )

chat_conversation_agent = initialize_agent(
    agent="chat-conversational-react-description",
    tools=tools,
    llm=llm,
    verbose=True,
    # max_iterations=5,
    memory=memory
)

