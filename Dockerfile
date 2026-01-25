# 1. Base Image: Use a lightweight, official Python version
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy only the requirements first (Caching Strategy)
# This makes rebuilding faster if you only change code, not libraries.
COPY requirements.txt .

# 4. Install dependencies
# We install 'build-essential' because 'posix_ipc' sometimes needs a C compiler
RUN apt-get update && apt-get install -y build-essential \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy the rest of the source code
COPY . .

# 6. Default command (This is a placeholder; docker-compose will override it)
CMD ["python", "-m", "logic_agent.agent"]