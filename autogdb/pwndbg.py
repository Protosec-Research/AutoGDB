from langchain.tools import tool
from pathlib import Path

CUR_DIR = Path(__file__).parent
DOCS_DIR = CUR_DIR/'docs'/'pwndbg'

def base_prompt() -> str:
    return open(DOCS_DIR/'index.md').read()

@tool("Read Command Docs")
def read_command_docs(md_path:str):
    """
    Read the docs of the command.
    :param md_path: The path to the markdown file to read. E.G. asm/asm.md
    """
    p = DOCS_DIR/md_path
    if not p.exists():
        return "No such file"
    return p.read_text()

if __name__ == '__main__':
    print(base_prompt())
    print(read_command_docs._run('asm/asm.md'))