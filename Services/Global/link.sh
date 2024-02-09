#!/bin/bash


# Remove files if they exist
rm app.py
rm auth.py
rm templates/base.html
rm templates/layout.html
rm requirements.txt
rm Dockerfile

# Create symbolic links (hard links)
ln ../Global/app.py app.py
ln ../Global/auth.py auth.py
mkdir -p templates
ln ../Global/templates/base.html templates/base.html
ln ../Global/templates/layout.html templates/layout.html
ln ../Global/requirements.txt requirements.txt
ln ../Global/Dockerfile Dockerfile
