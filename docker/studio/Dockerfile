FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CHANNEL_PLAY_STUDIO_DOCKER=1 \
    CHANNEL_PLAY_STUDIO_ALLOW_REMOTE=1 \
    CHANNEL_PLAY_STUDIO_HOST=0.0.0.0 \
    CHANNEL_PLAY_STUDIO_PORT=8776

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY tools/studio/docker/entrypoint.sh /usr/local/bin/channel-play-studio
RUN chmod +x /usr/local/bin/channel-play-studio

EXPOSE 8776

CMD ["channel-play-studio"]
