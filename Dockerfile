
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer cron, sqlite3 et procps pour ps/pgrep
RUN apt-get update && \
    apt-get install -y cron sqlite3 curl procps && \
    rm -rf /var/lib/apt/lists/*

COPY . .

# Crée le fichier de log pour cron
RUN touch /var/log/cron.log

# Ajout du job cron
COPY cronjob.txt /etc/cron.d/scrape-cron
RUN chmod 0644 /etc/cron.d/scrape-cron && crontab /etc/cron.d/scrape-cron

# Script de démarrage
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
