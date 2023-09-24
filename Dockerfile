FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install requests

CMD ["python", "iss_tracker.py"]
