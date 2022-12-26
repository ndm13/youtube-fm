FROM python:3.8-slim
COPY ../requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
RUN pip install waitress
COPY ../server /app/server
COPY ../core /app/core
EXPOSE 8000
CMD ["waitress-serve", "--host", "0.0.0.0", "--call", "server:create_app"]
