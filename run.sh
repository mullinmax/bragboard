#!/bin/bash
compose_file="compose.yml"

echo "Stopping and removing containers..."
sudo docker compose -f $compose_file down

echo "Building ingest and webui services..."
sudo docker compose -f $compose_file up --build --remove-orphans

echo "Stopping and removing containers..."
sudo docker compose -f $compose_file down
