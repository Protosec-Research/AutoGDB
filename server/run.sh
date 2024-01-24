PORT=8000

if [ ! -z "$1" ] # first argument(optional) determines the port number
then
    PORT=$1
fi

uvicorn main:app --host 0.0.0.0 --port $PORT --reload