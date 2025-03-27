# Use an official Python runtime as a parent image
FROM python:3.10-slim 

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
# COPY data/ data/
COPY src/ src/
COPY pyproject.toml .


# Install any needed packages specified in pyproject.toml
RUN pip install --no-cache-dir .

# Make port 80 available to the world outside this container
EXPOSE 8501

# Define environment variable
# ENV NAME = MinervAI

# Run app.py when the container launches
CMD ["streamlit", "run", "src/minervai/app.py"]