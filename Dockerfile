# --------------------------------------------------------
# Dockerfile to force Python 3.11 for Render deployment
# --------------------------------------------------------
FROM python:3.11-slim

# set working directory
WORKDIR /app

# copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of your app
COPY . .

# expose Render port
ENV PORT=10000

# start FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
