FROM node:lts

WORKDIR /app

RUN apt-get update && apt-get install python3-pip python3-venv -y
RUN python3 -m venv .venv

COPY requirements.txt .
RUN .venv/bin/pip3 install -r requirements.txt

WORKDIR /app/client

COPY client/package*.json .
RUN npm install

COPY . ..

RUN npm run build

WORKDIR /app

EXPOSE 3001

CMD [ ".venv/bin/python3", "server.py" ]