FROM python:3.12-bookworm

RUN useradd -m nikobot \
  && mkdir /home/nikobot/src \
  && chown nikobot /home/nikobot/src

COPY --chown=nikobot --chmod=755 requirements.txt /home/nikobot/requirements.txt

# install pip packages
RUN pip install --upgrade -r /home/nikobot/requirements.txt

COPY --chown=nikobot --chmod=755 src/ /home/nikobot/src/

WORKDIR /home/nikobot

USER nikobot

ENTRYPOINT [ "python3", "src/main.py", "--config", "./config.json" ]
