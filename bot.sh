#!/bin/bash
docker stop bot
docker rm bot
docker run -d --name bot -v /path/to/config/folder:/config --restart always popurisiva/binancebot:latest