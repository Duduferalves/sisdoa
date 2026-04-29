# SisDoa - Sistema de Controle de Doações
# Dockerfile para execução em container

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install dependencies and the project
RUN uv sync --frozen

# Set the entrypoint to the sisdoa CLI
ENTRYPOINT ["uv", "run", "sisdoa"]

# Default command shows help
CMD ["--help"]
