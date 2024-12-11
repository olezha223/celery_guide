FROM redis:6.0.16

RUN apt-get update && apt-get install -y gettext-base