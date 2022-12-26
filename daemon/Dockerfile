FROM python:3.8-alpine
COPY ../requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY ../daemon /app/daemon
COPY ../core /app/core
CMD ["python", "-m", "daemon"]