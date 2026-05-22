# Laboratory Work 1

## Topic

Introduction to Docker containerization.

## Description

This project contains a simple Flask web application running inside a Docker container.

## Endpoints

- `GET /` - returns a text message
- `GET /health` - returns application status in JSON format

## Build Docker image

```bash
docker build -t lab1-docker-app .
```

## Run Docker container

```bash
docker run -p 5000:5000 lab1-docker-app
```

## Test with curl

```bash
curl http://localhost:5000
curl http://localhost:5000/health
```