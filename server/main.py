from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

import httpx
import base64

def decode_response(encoded_text):
    base64_bytes = encoded_text.encode('utf-8')
    text_bytes = base64.b64decode(base64_bytes)
    return text_bytes.decode('utf-8')

SERVER = "http://192.168.31.251:5000"
instructions_list = []

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
    
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

import re

def remove_ansi_escape_sequences(text):
    # ANSI 转义序列的正则表达式模式
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

@app.post("/see-callback/")
async def see_callback(request: Request):
    item = await request.json()
    results_dict[item['instruction']] = remove_ansi_escape_sequences(decode_response(item['response']))
    return {"message": "Response received successfully"}

import httpx
import asyncio

results_dict = {}

async def add_instruction(instruction: str):
    async with httpx.AsyncClient() as client:
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
