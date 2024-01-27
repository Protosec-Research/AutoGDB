from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

import httpx
import base64

def decode_bs64(encoded_text):
    base64_bytes = encoded_text.encode('utf-8')
    text_bytes = base64.b64decode(base64_bytes)
    return text_bytes.decode('utf-8')

def encode_bs64(text):
    text_bytes = text.encode('utf-8')
    base64_bytes = base64.b64encode(text_bytes)
    return base64_bytes.decode('utf-8')

import os
import json
CACHE_FILE_PATH = '../.server_cache.autogdb.json'
def get_server_info():
    if os.path.exists(CACHE_FILE_PATH):
        with open(CACHE_FILE_PATH, 'r') as cache_file:
            server_info = json.load(cache_file)
            addr = server_info['ip']
            port = server_info['port']
                
            if (not addr) or (not port):
                raise KeyError(f"Server address and port saved is empty, please save it again by deleting:{CACHE_FILE_PATH}")
                
            return addr,port
                
            # except json.JSONDecodeError:
            #     print("Cache file is corrupted. Please enter server details again.")

ip,port = get_server_info()
SERVER = f"http://{ip}:{port}"
instructions_list = []
current_binary = None

app = FastAPI()
templates = Jinja2Templates(directory="templates")  # Make sure 'templates' directory exists

# Simulated database of instructions
instructions_queue = []


@app.get("/add-instruction/")
async def add_instruction(instruction: str):
    instructions_queue.append(instruction)
    return JSONResponse(content={"message": "Instruction added successfully"}, status_code=200)

@app.get("/get-instruction")
async def get_instruction():
    if instructions_queue:
        # Pop the first instruction from the queue and return it
        instruction = instructions_queue.pop(0)
        return {"instruction": instruction}
    else:
        # If the queue is empty, return an empty instruction
        raise HTTPException(status_code=404, detail="No instruction available.")
        # return {"instruction": 'No current instruction'}
    
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

import re

def remove_ansi_escape_sequences(text):
    ansi_escape_pattern = re.compile(r'''
        \x1B  # ESC
        (?:   # 7-bit C1 Fe (except CSI)
            [@-Z\\-_]
        |     # or [ for CSI, followed by a control sequence
            \[
            [0-?]*  # Parameter bytes
            [ -/]*  # Intermediate bytes
            [@-~]   # Final byte
        )
    ''', re.VERBOSE)
    return ansi_escape_pattern.sub('', text)

class NewConnectedBinary:

    def __init__(self,name,path) -> None:
        self.name = name
        self.path = path

@app.get("/test-connection-gdb/")
async def test_connection_gdb(binary_name: str,binary_path: str):
    global current_binary
    current_binary = NewConnectedBinary(name=binary_name,path=binary_path)
    return {"message": "success"}

@app.get("/test-connection-cli/")
async def test_connection_cli():
    if current_binary == None:
        return {"message": "failed", "detail": "No binary is in-use"}
    return {"message": "success",
            "binary_name":current_binary.name,
            "binary_path": current_binary.path
            }

@app.post("/see-callback/")
async def see_callback(request: Request):
    item = await request.json()
    res = remove_ansi_escape_sequences(decode_bs64(item['response']))
    # if len(res) > 2040:
    #     notion = "Since the respone is too long, only first 2040 is noted."
    #     results_dict[item['instruction']] = notion + res[:(2040-len(notion))]
    #     return {"message": "Response received successfully, but too long"}
    results_dict[item['instruction']] = remove_ansi_escape_sequences(decode_bs64(item['response']))
    return {"message": "Response received successfully"}

import httpx
import asyncio

results_dict = {}

async def add_instruction(instruction: str):
    async with httpx.AsyncClient(trust_env=False) as client:
        response = await client.get(f"{SERVER}/add-instruction/?instruction={instruction}")
        if response.status_code == 200:
            print(f"Instruction '{instruction}' added successfully.")
        else:
            raise Exception(f"Failed to add instruction: {response.text}")

async def await_callback(instruction: str):
    while instruction not in results_dict:
        await asyncio.sleep(3)
    return results_dict.pop(instruction)

@app.post("/instruct/")
async def instruct(instruction: str):
    await add_instruction(instruction)
    response = await await_callback(instruction)
    print(f"Received response for instruction '{instruction}': {response}")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
