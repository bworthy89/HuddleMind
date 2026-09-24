FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY deploy/requirements.txt /app/deploy/requirements.txt
RUN pip install --no-cache-dir -r deploy/requirements.txt \
    && useradd --uid 10001 --create-home huddlemind \
    && mkdir /data && chown huddlemind:huddlemind /data
COPY bridge /app/bridge
USER huddlemind
EXPOSE 8080
CMD ["python", "-m", "bridge.hosted_receiver"]
