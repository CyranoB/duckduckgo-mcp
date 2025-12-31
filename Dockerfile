FROM python:3.12-slim

WORKDIR /app

# Version for setuptools_scm (required since .git is not copied)
# Override at build time with: docker build --build-arg VERSION=x.y.z
ARG VERSION=0.0.0
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION}

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Run the MCP server
ENTRYPOINT ["duckduckgo-mcp", "serve"]
