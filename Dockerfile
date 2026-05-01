# TODO: Write a production-ready Dockerfile
#
# All of these are tested by the grader:
#
# [ ] Multi-stage build (2+ FROM instructions)
# [ ] Base image: python:3.14-slim (pinned version, no :latest)
# [ ] Copy requirements.txt and pip install BEFORE copying source code (layer caching)
# [ ] Run as a non-root USER
# [ ] EXPOSE 8080
# [ ] HEALTHCHECK instruction
# [ ] No hardcoded secrets (no ENV PASSWORD=..., no ENV SECRET_KEY=...)
# [ ] Final image under 200MB
#
# Start command: uvicorn src.app:app --host 0.0.0.0 --port 8080
