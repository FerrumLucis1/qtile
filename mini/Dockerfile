# Browser-accessible demo of qtile-mini. Build from the repo root:
#   docker build -f mini/Dockerfile -t qtile-mini .
#   docker run --rm -p 8080:8080 qtile-mini     ->  http://localhost:8080/vnc.html?autoconnect=true&resize=scale
FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive PIP_BREAK_SYSTEM_PACKAGES=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
      xvfb x11vnc novnc websockify xterm fonts-dejavu-core \
      python3 python3-pip python3-dev gcc libffi-dev libxcb1 libpango-1.0-0 libpangocairo-1.0-0 libcairo2 \
      libglib2.0-0 shared-mime-info \
  && pip install qtile xcffib cairocffi pangocffi \
  && apt-get purge -y gcc python3-dev && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man
COPY mini/config.py /app/config.py
COPY mini/start.sh /app/start.sh
RUN useradd -m demo && chmod +x /app/start.sh
USER demo
ENV PORT=8080
EXPOSE 8080
CMD ["/app/start.sh"]
