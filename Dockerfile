FROM python:3.13-slim

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* README.md /app/

# Copy application code
COPY src /app/src/

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi

EXPOSE 8008
EXPOSE 9080

# Command to run the API
ENTRYPOINT ["uvicorn"]
CMD ["src.api.main:app", "--host", "0.0.0.0", "--port", "8008", "--reload"]
