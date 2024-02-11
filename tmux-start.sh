#!/bin/bash

# Kill tmux sessions if they exist
tmux kill-session -t "auth"
tmux kill-session -t "care"
tmux kill-session -t "finance"
tmux kill-session -t "cloud"
tmux kill-session -t "records"
tmux kill-session -t "prescriptions"
tmux kill-session -t "portal"

# Kill local-haproxy container if it exists
docker stop haproxy

# Start tmux sessions
tmux new-session -d -s "auth" -n "Auth" "source venv/bin/activate && cd Services/Auth &&  DEBUG=TRUE python app.py && sh"
tmux new-session -d -s "care" -n "CareConnect" "source venv/bin/activate && cd Services/CareConnect &&  DEBUG=TRUE python app.py"
tmux new-session -d -s "finance" -n "FinCare" "source venv/bin/activate && cd Services/FinCare &&  DEBUG=TRUE python app.py"
tmux new-session -d -s "cloud" -n "MediCloud" "source venv/bin/activate && cd Services/MediCloud &&  DEBUG=TRUE python app.py"
tmux new-session -d -s "records" -n "MedRecords" "source venv/bin/activate && cd Services/MedRecords &&  DEBUG=TRUE python app.py"
tmux new-session -d -s "prescriptions" -n "Prescriptions" "source venv/bin/activate && cd Services/Prescriptions &&  DEBUG=TRUE python app.py"
tmux new-session -d -s "portal" -n "Portal" "source venv/bin/activate && cd Services/Portal &&  DEBUG=TRUE python app.py"

pwd
# Start haproxy
docker run --rm -d -p 443:443 -p 80:80 --name haproxy -v ./haproxy/local-haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg -v ./haproxy/certs:/etc/ssl/certs haproxy:latest
