# Use Python 3.13
FROM python:3.13-slim

ARG PROJECT_PATH=""
# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy the entire project including libs
COPY . .

WORKDIR /app/${PROJECT_PATH}
# Create virtual environment and install dependencies
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv sync --all-extras --no-editable

# Set environment variables
ENV PYTHONPATH=/app/${PROJECT_PATH}:/app/libs
ENV PATH="/app/.venv/bin:$PATH"

# Run main.py
ENTRYPOINT ["uv", "run", "main.py"]
