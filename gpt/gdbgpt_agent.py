# weather_agent.py
# Import things that are needed generically

from langchain.agents import initialize_agent
from langchain.llms import OpenAI
from langchain import LLMChain
from langchain.prompts import PromptTemplate

# import custom tools
from instruct_gdb import Gdbgpt



llm = OpenAI(temperature=0.5,
            model_name='gpt-4-1106-preview',
            openai_api_base="https://ai-yyds.com/v1",
            openai_api_key="sk-5tzrrbESxAWLDppg39B7DaF0F5B94b69A47e570d3e930804"
            )

prompt = PromptTemplate(
    input_variables=[],
    template="""\
    You are a serious CTF player who don't make reckless decision. \
    * Use continue, but never use run \
    * You are inside of gdb (in pwndbg version) \
    * The file is currently loaded, and paused in a certain frame\
    * You can use commands like stack, heap, that is built in pwndbg version of gdb
    """
)

# Load the tool configs that are needed.
llm_gdb_chain = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=True
)

tools = [
    Gdbgpt
]

# Construct the react agent type.
agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=True
)

agent.run("Seek way to exploit this file, Generate the final payload")