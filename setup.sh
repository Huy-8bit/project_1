python3.9 -m venv virtualenv
source virtualenv/bin/activate
python3.9 -m pip install -r requirements.txt
cd api
python3.9 manage.py runserver
