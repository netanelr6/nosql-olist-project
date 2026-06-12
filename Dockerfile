FROM python:3.10-slim

WORKDIR /app

# העתקה והתקנה של החבילות
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# העתקת שאר קוד הפרויקט לקונטיינר
COPY . .