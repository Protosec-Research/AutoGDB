from langchain.agents import Tool
import httpx
import asyncio

SERVER = "192.168.31.251:5000"
async def gdb_send(command: str = None) -> str:
    """
    Sends a command to a local server and awaits the response.
    The command is sent as a query parameter 'instruction' to the '/instruct/' endpoint.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            'http://localhost:5000/instruct/',
            params={'instruction': command},
            headers={'accept': 'application/json'}
        )
        response.raise_for_status() 
        return response.text
    
def gdb_run(command: str = None) -> str:
    return asyncio.run(gdb_send(str(command)))


Gdbgpt = Tool(
    name="gdb",
    func=gdb_run,
    description="run gdb commands on this binary file on this specific frame in gdb, given arguments: command(gdb or pwndbg command)"
)