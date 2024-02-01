#!/bin/bash

# Kill tmux sessions if they exist
tmux kill-session -t "auth"
tmux kill-session -t "care"
tmux kill-session -t "finance"
tmux kill-session -t "cloud"
tmux kill-session -t "records"
tmux kill-session -t "prescriptions"

# Change directory to the root of the project
cd Services

# Start tmux sessions
tmux new-session -d -s "auth" -n "Auth" "cd Auth && python app.py"
tmux new-session -d -s "care" -n "CareConnect" "cd CareConnect && python app.py"
tmux new-session -d -s "finance" -n "FinCare" "cd FinCare && python app.py"
tmux new-session -d -s "cloud" -n "MediCloud" "cd MediCloud && python app.py"
tmux new-session -d -s "records" -n "MedRecords" "cd MedRecords && python app.py"
tmux new-session -d -s "prescriptions" -n "Prescriptions" "cd Prescriptions && python app.py"

