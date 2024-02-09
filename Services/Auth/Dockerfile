FROM python:3.7.4-slim-buster

# Set the working directory to /app
WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt


COPY . /app

EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "app.py"]
