
FROM python:3.9

WORKDIR /app

RUN apt-get update && apt-get install -y redis-server

COPY requirements.txt .

RUN python -m venv lib
RUN /bin/bash -c "source lib/bin/activate"

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000


# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]