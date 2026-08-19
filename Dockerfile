FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py config.py ./
COPY core ./core

EXPOSE 8500

HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8500/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8500", "--server.address=0.0.0.0"]
