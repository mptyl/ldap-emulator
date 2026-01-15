FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data and keys directories
RUN mkdir -p /app/data /app/keys

# Expose port
EXPOSE 8029

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8029"]
