# --- STAGE 1: Builder ---
# We use a specific version of python on a minimal 'slim' base.
# We name this stage 'builder' so we can reference it later.
# (Fixed casing on 'FROM' and 'as' to remove build warning)
FROM python:3.10-slim AS builder

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file *first*
# This takes advantage of Docker's layer caching.
# If requirements.txt doesn't change, Docker won't re-run pip install.
COPY requirements.txt .

# Install the Python dependencies
# --no-cache-dir: Disables the cache, resulting in a smaller image size
# We create a virtual environment for a clean dependency install.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt


# --- STAGE 2: Final Image ---
# Start from a fresh, minimal base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Create a non-root user 'appuser' for security
# Running containers as root is a major security risk.
RUN useradd -m appuser
USER appuser

# Copy the virtual environment (with dependencies) from the 'builder' stage
COPY --chown=appuser:appuser --from=builder /opt/venv /opt/venv

# Copy the application code
COPY --chown=appuser:appuser app.py .

# Set environment variables for Flask
# FLASK_APP: Tells Flask where your application is
# FLASK_RUN_HOST: Makes the server accessible from outside the container
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
# Add the venv to the PATH
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port Flask runs on (default is 5000)
EXPOSE 5000

# Define the command to run the application
# We are changing this to run Python directly, bypassing 'flask run'
# This will execute the if __name__ == '__main__': block in app.py
CMD ["python", "app.py"]

