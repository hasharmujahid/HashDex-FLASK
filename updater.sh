#!/bin/bash

# Directory where your app and Git repository are located
APP_DIR="$(pwd)"
GIT_REPO="https://github.com/hasharmujahid/HashDex.git"
BRANCH="main"  # Replace with the desired branch name

# Function to update the app from Git and restart it
update_and_restart() {
    cd "$APP_DIR"
    echo "Pulling latest changes from Git..."
    git pull origin "$BRANCH"
    
    echo "Restarting the app..."
    pkill -f "python3 app.py"  # Kill the existing app process
    nohup python3 app.py > app.log 2>&1 &
    echo "App restarted."
}

# Initial update and restart
update_and_restart

# Loop to repeat every 1 hour
while true; do
    sleep 3600  # Sleep for 1 hour (3600 seconds)
    update_and_restart
done