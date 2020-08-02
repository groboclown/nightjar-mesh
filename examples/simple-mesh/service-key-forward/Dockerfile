FROM alpine:3.8

EXPOSE 3000

COPY . /home/app

# Installs curl to allow for internal health checks.

RUN echo "Starting install..." \
  && apk --update add nodejs npm curl \
  && cd /home/app \
  && npm install \
  && echo "Install complete."

WORKDIR /home/app
CMD ["node", "index.js"]
