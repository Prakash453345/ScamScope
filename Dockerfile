FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Build the Vector Database during the Docker build process
RUN python ingest.py

# HuggingFace Spaces Docker deployments expose port 7860
ENV PORT=7860
EXPOSE 7860

# Start the Flask app with Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860", "--workers", "2", "--threads", "4", "--timeout", "120"]
