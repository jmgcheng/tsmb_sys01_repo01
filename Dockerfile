# Use the official Python image from the Docker Hub
FROM python:3.12.4-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc python3-dev build-essential cron \
    wget lsb-release gnupg2

# Add PostgreSQL's official APT repository for version 16
RUN echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

# Update package lists and install the PostgreSQL client version 16
RUN apt-get update && apt-get install -y postgresql-client-16

# Install pip requirements
COPY core/requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY core /app/

# Define build arguments
ARG DATABASE_TSMBSYS_NAME
ARG DATABASE_TSMBSYS_USER
ARG DATABASE_TSMBSYS_PASSWORD
ARG DATABASE_TSMBSYS_HOST
ARG DATABASE_TSMBSYS_PORT
ARG DOCKER_ENV
ARG DJANGO_SECRET_KEY_TSMB_SYS01

# Set environment variables
ENV DATABASE_NAME=$DATABASE_TSMBSYS_NAME
ENV DATABASE_USER=$DATABASE_TSMBSYS_USER
ENV DATABASE_PASSWORD=$DATABASE_TSMBSYS_PASSWORD
ENV DATABASE_HOST=$DATABASE_TSMBSYS_HOST
ENV DATABASE_PORT=$DATABASE_TSMBSYS_PORT
ENV DOCKER_ENV=$DOCKER_ENV
ENV DJANGO_SECRET_KEY_ISI=$DJANGO_SECRET_KEY_TSMB_SYS01

COPY shscripts /shscripts

RUN chmod +x /shscripts/entrypoint.sh

ENTRYPOINT ["/shscripts/entrypoint.sh"]