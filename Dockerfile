FROM python:3.8
WORKDIR /usr/src/app

COPY . ./AutoGDB
WORKDIR /usr/src/app/AutoGDB
RUN python3 -m pip install -r requirements.txt

WORKDIR /usr/src/app/AutoGDB/server
RUN chmod +x ./run.sh

EXPOSE 5000
ENV YOUR_SERVER_IP=127.0.0.1
ENV YOUR_SERVER_PORT=5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]

