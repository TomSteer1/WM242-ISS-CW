#!/bin/bash

mkdir -p DBs

# Check database files and create if not exists
# Auth 
if [ ! -f DBs/auth.db ]; then
		touch DBs/auth.db
fi
# CareConnect
if [ ! -f DBs/careconnect.db ]; then
		touch DBs/careconnect.db
fi
# Finance
if [ ! -f DBs/finance.db ]; then
		touch DBs/finance.db
fi
# Cloud
if [ ! -f DBs/cloud.db ]; then
		touch DBs/cloud.db
fi
# Records
if [ ! -f DBs/records.db ]; then
		touch DBs/records.db
fi
# Portal
if [ ! -f DBs/portal.db ]; then
		touch DBs/portal.db
fi
# Prescriptions
if [ ! -f DBs/prescriptions.db ]; then
		touch DBs/prescriptions.db
fi

mkdir -p files

# Build docker images
docker-compose build

# Start the containers
docker-compose up
