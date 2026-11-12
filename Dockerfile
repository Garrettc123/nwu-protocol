# NWU staging node-four canary: signed health only.
# Explicitly excludes NWU's blockchain backends, consensus, settlement and token processes.
FROM python:3.11-alpine
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY nwu_protocol/mesh_heartbeat.py /app/mesh_heartbeat.py
USER 65532:65532
CMD ["sh", "-c", "while true; do python -u /app/mesh_heartbeat.py; sleep 300; done"]
