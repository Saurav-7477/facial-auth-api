# Use official Python base image
FROM python:3.10

# Set working directory inside the container
WORKDIR /app

# Copy the project files to the container
COPY . .

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirement.txt

# Expose the port the app runs on
EXPOSE 8000

# Start the Django application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "facial_auth.wsgi"]
