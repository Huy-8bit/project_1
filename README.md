# `project_1`


## `requirements`
python 3.9 - mongodb local
redis server

## `How to run`

### `run with docker`

```bash
# build docker image 
docker-compose up --build
```

### `run with python and redis on host machine`

```bash

# start redis server with docker
docker container run -d --name redis -p 6379:6379 redis:latest

# start mongodb server with docker
docker container run -d --name mongo -p 27017:27017 mongo:latest


# create virtual environment
python -m venv lib

# activate virtual environment
source lib/bin/activate

# install dependencies
pip install -r requirements.txt

#run server
uvicorn main:app --reload

```




## License
[Source code](https://github.com/Huy-8bit/project_1)