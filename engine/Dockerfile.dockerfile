#Use official Python runtime as a parent image
FROM python:3.10-slim

#Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#Set work directory
WORKDIR /app

#Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

#Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

#Copy application code
COPY . /app/

#Expose port (if applicable)
EXPOSE 8080

#Run the application
CMD ["python", "main.py"]