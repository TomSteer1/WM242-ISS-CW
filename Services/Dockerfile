FROM python:3.7.4-slim-buster

# Set the working directory to /app
WORKDIR /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

EXPOSE 5000
EXPOSE 5001
EXPOSE 5002
EXPOSE 5003
EXPOSE 5004

# Run app.py when the container launches
CMD ["python", "app.py"]
