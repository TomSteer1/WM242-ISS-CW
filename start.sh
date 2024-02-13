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


if [ ! -f Services/Auth/.env ]; then
	cp Services/Auth/.env.example Services/Auth/.env 
fi

if [ ! -f Services/CareConnect/.env ]; then
	cp Services/CareConnect/.env.example Services/CareConnect/.env 
fi

if [ ! -f Services/FinCare/.env ]; then
	cp Services/FinCare/.env.example Services/FinCare/.env 
fi

if [ ! -f Services/MediCloud/.env ]; then
	cp Services/MediCloud/.env.example Services/MediCloud/.env 
fi

if [ ! -f Services/MedRecords/.env ]; then
	cp Services/MedRecords/.env.example Services/MedRecords/.env 
fi

if [ ! -f Services/Portal/.env ]; then
	cp Services/Portal/.env.example Services/Portal/.env 
fi

if [ ! -f Services/Prescriptions/.env ]; then
	cp Services/Prescriptions/.env.example Services/Prescriptions/.env 
fi

mkdir -p files

# Build docker images
docker-compose build

# Start the containers
docker-compose up
