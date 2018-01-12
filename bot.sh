#!/bin/bash
docker stop bot
docker rm bot
docker run -d --name bot -v /Users/sivapopuri/dev/personal/bots/utk/config:/config --restart always jufkes/kucoinbot:latest