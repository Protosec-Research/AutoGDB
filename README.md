# GDB <3 GPT

## What is this?
This is a project that focused on combining the power of ChatGPT on reverse-engineering, binary-exploition jobs. This includes

* `/plugin` **the plugin that your gdb needs to connect to your server**
* `/server` **fastapi backend server**, use to dealt with you infomation and gpts, acts like a bridge in between
* `/gpt` gpt function calls and demo

# Setup Server-side

```shell
python3 -m pip install -r requirements.txt && chmod +x ./run.sh
```
after installing requirements, you can run the server by `./run.sh`


# GDB Plugin

*(BE NOTICED THAT THE PLUGIN AUTOMATIC ESCAPE ANY PROXY SETTINGS, SINCE THIS VERSION OF GDB <3 GPT IS MENT TO RUN UNDER LOCAL LOCALHOST)*

Download it & load it & use it
```shell
echo "/YOUR/PATH/TO/gdb-s-gpt/plugin/gpt.py" >> ~/.gdbinit
```

In you `gdb` or `pwndbg`, You can run:
```shell
pwndbg> gdbgpt <YOUR_SERVER_IP> <YOUR_SERVER_PORT>
```
* `YOUR_SERVER_IP` : Your ip for the backend server
* `YOUR_SERVER_PORT` : Port for this server

