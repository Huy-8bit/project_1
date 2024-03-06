
FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN python -m venv lib

RUN /bin/bash -c "source lib/bin/activate"

RUN pip install -r requirements.txt
RUN pip install PyJWT

RUN mkdir -p data/key data/encrypted_files

COPY . .

EXPOSE 8000


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]