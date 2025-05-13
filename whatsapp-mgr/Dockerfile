FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

# Install pip dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make the script executable
RUN chmod +x app.py

# Set the entrypoint to the Python script
ENTRYPOINT ["python", "app.py"]

# Default command can be overridden when running the container
CMD []