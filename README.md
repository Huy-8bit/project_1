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

# start redis server
redis-server

# create virtual environment
python -m venv lib

# activate virtual environment
source lib/Scripts/activate

# install dependencies
pip install -r requirements.txt

#run server
uvicorn main:app --reload

```




## License
[Source code create by Huy8bit](https://github.com/Huy-8bit/Cloud-Backup-System)