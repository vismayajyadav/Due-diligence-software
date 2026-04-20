# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY ./backend/requirements.txt /app/

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code into the container at /app
# This includes the api and ai_modules directories
COPY ./backend /app/backend

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable (optional, can be set at runtime)
# ENV FLASK_APP=backend.api.app:app
# ENV FLASK_RUN_HOST=0.0.0.0

# Run app.py when the container launches
# Use gunicorn for production deployment (install it via requirements.txt if needed)
# CMD ["flask", "run", "--host=0.0.0.0"]
# Example using gunicorn (add gunicorn to requirements.txt first):
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "backend.api.app:app"]
# For simplicity in demonstration, using Flask's built-in server:
CMD ["python", "backend/api/app.py"]

