#!/bin/bash
cd ~/reddit
docker compose pull
docker compose down
docker compose up -d --build
