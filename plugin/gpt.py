import gdb
import requests
import time

import gdb
import os
import signal

session_without_proxies = requests.Session()
session_without_proxies.trust_env = False
# This is without proxy; only for testing

import base64

def encode_response(text):
    text_bytes = text.encode('utf-8')
    base64_bytes = base64.b64encode(text_bytes)
    return base64_bytes.decode('utf-8')


def send_response(response, command,success=False):
    try:
        # Adjust the field names if necessary to match the expected schema
        json_payload = {"response": encode_response(response), "instruction": command}
        rs = session_without_proxies.post(f"http://{SERVER}/see-callback/", json=json_payload)
        # Now use without proxies
        if rs.status_code == 200:
            print("[*] Response sent successfully.")
        else:
            print(f'Send_response failed, check for server connection please: {rs.status_code}')
    except Exception as e:
        print(f'Exception occurred while sending response: {e}')


class GdbGptCommand(gdb.Command):
    "Fetch and execute commands from a remote server"

    def __init__(self):
        super(GdbGptCommand, self).__init__("gdbgpt", gdb.COMMAND_USER)
        self.server = None
        self.port = None

    def test_connection(self):
        server_url = f"http://{self.server}:{self.port}"
        try:
            response = session_without_proxies.get(f"{server_url}/test-connection/", timeout=3)
            if response.status_code == 200:
                print(f"Connection to {server_url} successful. Status Code: {response.status_code}")
            else:
                print(f"Connection to {server_url} failed. Status Code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Connection to {server_url} failed. Error: {e}")
    

    def invoke(self, arg, from_tty):
        if arg:
            args = arg.split()
            if len(args) == 2:
                self.server, self.port = args
                self.test_connection()
            else:
                print("Usage: gdbgpt <server> <port>")
                return
        else:
            print("Usage: gdbgpt <server> <port>\cnNo server and port provided.")
            return

        server_url = f"http://{self.server}:{self.port}"
        while True:
            try:
                response = session_without_proxies.get(f"http://{server_url}/get-instruction", timeout=30)
                time.sleep(2)
                if response.status_code == 200:
                    data = response.json()
                    instruction = str(data.get('instruction'))
                    if instruction:
                        print(f"[*] Executing instruction from server: {instruction}")
                        try:
                            # Attempt to execute the instruction and capture the output.
                            responses = gdb.execute(instruction, to_string=True)
                            print(responses)
                            send_response(response=responses, command=instruction)
                        except gdb.error as e:
                            error_message = str(e)
                            error_message = f"[!] An error occurred: {error_message}"
                            error_message = str(error_message)
                            print(error_message)
                            send_response(response=error_message, command=instruction, success=False)

                else:
                    if response.status_code == 404:
                        pass
                    else:
                        print(f"Failed to connect to server. Status Code: {response.status_code}")

            except Exception as e:
                print(f"An error occurred: {e}")
                time.sleep(2)

GdbGptCommand()