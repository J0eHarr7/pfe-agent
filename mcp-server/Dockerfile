FROM python:3.12-slim

WORKDIR /app

# Install TeX Live (full LaTeX distribution) + utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-full \
    texlive-lang-arabic \
    texlive-lang-french \
    latexmk \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Workspace for .tex and .pdf files
RUN mkdir -p /workspace

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
