# 1) Build stage: install mkdocs & build the site
FROM python:3.11-slim AS docs-builder

# Install mkdocs + theme
RUN pip install --no-cache-dir \
    mkdocs \
    mkdocs-material \
    mkdocs-swagger-ui-tag

WORKDIR /docs-build

# copy the root-level config
COPY mkdocs.yml .

# copy the markdown sources from mkdocs/docs into a ./docs folder
COPY mk_docs ./mk_docs

# now build into /site
RUN mkdocs build --site-dir /site

# 2) Final stage: install your app & copy the built site
FROM python:3.11-slim

# Create a non-root user for safety (optional)
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy only requirements first for better cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . /app

# Copy the MkDocs‐built static site from the builder into /app/site
COPY --from=docs-builder /site /app/site

# Make sure the log file exists and is owned by appuser
RUN touch /app/tpi_api.log \
 && chown appuser:appgroup /app/tpi_api.log

# Expose port ...
EXPOSE 80

# Switch to non-root
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]