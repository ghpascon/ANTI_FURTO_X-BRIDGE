FROM python:3.11.0-slim

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Disable virtualenv inside container
RUN poetry config virtualenvs.create false

# Copy only dependency files first (better cache)
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-root --no-interaction --no-ansi

# Copy application code
COPY . .

EXPOSE 5000

CMD ["python", "main.py"]
