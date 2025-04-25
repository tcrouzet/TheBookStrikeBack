#!/bin/bash
#chmod +x git.sh
current_date=$(date +"%Y-%m-%d %H:%M:%S")

# git fetch origin
# git diff origin/main
# git pull origin main

git add .
git commit -m "sync $current_date"
git pull origin main
git push -u origin main