FROM python:3.12-bookworm

RUN apt-get update \
  && useradd -m nikobot \
  && mkdir /home/nikobot/src \
  && chown nikobot /home/nikobot/src

COPY --chown=nikobot --chmod=755 src/ /home/nikobot/src/
COPY --chown=nikobot --chmod=755 requirements.txt /home/nikobot/requirements.txt

# install pip packages
RUN pip install -r /home/nikobot/requirements.txt

USER nikobot

ENTRYPOINT [ "python3", "/home/nikobot/src/main.py" ]
