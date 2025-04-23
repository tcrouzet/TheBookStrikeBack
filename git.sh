#!/bin/bash
#chmod +x git.sh
current_date=$(date +"%Y-%m-%d %H:%M:%S")
git add .
git commit -m "sync $current_date"
git push -u origin main