FROM python:3.12-slim
WORKDIR /app
COPY studio-app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY studio-app /app/studio-app
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "studio-app/server.py"]
