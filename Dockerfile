FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir python-telegram-bot==13.15 opencv-python numpy

COPY . .

CMD ["python", "bot.py"]