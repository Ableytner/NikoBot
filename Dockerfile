FROM python:3.12-bookworm

RUN apt-get update \
  && useradd -m nikobot

COPY --chown=nikobot --chmod=755 src requirements.txt /home/nikobot/

# install pip packages
RUN pip install -r /home/nikobot/requirements.txt

USER nikobot

ENTRYPOINT [ "python3 src/main.py" ]
