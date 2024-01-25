#/bin/sh
DIR=$(pwd)
chmod +r $DIR/plugin/gpt.py
echo "source $DIR/plugin/gpt.py" >> ~/.gdbinit