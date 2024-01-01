import gdb
import requests
import time

import gdb
import os
import signal

session_without_proxies = requests.Session()
session_without_proxies.trust_env = False
# This is without proxy; only for testing



def interrupt_program():
    """Sends a SIGINT to the debugged process to simulate Ctrl+C."""
    # 获取当前选中的进程
    inferior = gdb.selected_inferior()

    if inferior is not None and inferior.pid > 0:
        # 发送SIGINT信号到进程
        os.kill(inferior.pid, signal.SIGINT)
        print(f"Sent SIGINT to process with PID: {inferior.pid}")
    else:
        print("No process is currently being debugged.")

# 在GDB Python API中封装成命令
class InterruptCommand(gdb.Command):
    """Interrupt the execution of the debugged program (like Ctrl+C)"""

    def __init__(self):
        super(InterruptCommand, self).__init__("interrupt", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        interrupt_program()

InterruptCommand()

import base64

def encode_response(text):
    text_bytes = text.encode('utf-8')
    base64_bytes = base64.b64encode(text_bytes)
    return base64_bytes.decode('utf-8')

SERVER = "192.168.31.251:5000"

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


class ReverseShellCommand(gdb.Command):
    "Fetch and execute commands from a remote server"

    def __init__(self):
        super(ReverseShellCommand, self).__init__("gdbgpt", gdb.COMMAND_USER)
        self.set_asynchronous(True)

    def invoke(self, arg, from_tty):
        while True:
            try:
                response = session_without_proxies.get(f"http://{SERVER}/get-instruction", timeout=5)
                time.sleep(2)
                if response.status_code == 200:
                    data = response.json()
                    instruction = str(data.get('instruction'))
                    if instruction and (instruction != 'No current instruction'):
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
                    if response.status_code == 404 or (instruction == 'No current instruction'):
                        pass
                    else:
                        print(f"Failed to connect to server. Status Code: {response.status_code}")

            except Exception as e:
                print(f"An error occurred: {e}")
                time.sleep(2)

InterruptCommand()
ReverseShellCommand()