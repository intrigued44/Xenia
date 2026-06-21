FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements, convert from UTF-16 to UTF-8 and strip windows-specific libraries
COPY requirements.txt .
RUN python -c "content = open('requirements.txt', 'r', encoding='utf-16').read(); lines = [l for l in content.splitlines() if not any(w in l.lower() for w in ['win10toast', 'pywin32', 'pypiwin32', 'pygetwindow'])]; open('requirements_linux.txt', 'w', encoding='utf-8').write('\n'.join(lines))" \
    && pip install --no-cache-dir -r requirements_linux.txt

# Copy the rest of the application code
COPY . .

# Set default env variables
ENV PORT=8000
ENV ENV=production

EXPOSE 8000

# Start server
CMD ["uvicorn", "platform_core.server:app", "--host", "0.0.0.0", "--port", "8000"]
