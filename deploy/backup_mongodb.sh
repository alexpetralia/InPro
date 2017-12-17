#!/bin/bash

sudo docker exec -it mongodb mongodump --gzip --out /backups/`date "+%Y-%m-%d"`
