# IoT Simulator Dockerfile - To be implemented in Task 4
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy simulator script
COPY simulator.py .

# Run simulator
CMD ["python", "simulator.py"]
