#!/bin/bash

# Démarrer cron
echo "Starting cron..."
cron

# Attendre un peu (optionnel, pour debug)
sleep 2

# Vérifier que cron tourne
pgrep cron > /dev/null && echo "Cron is running." || echo "Cron failed to start."

# Démarrer Flask
echo "Starting Flask..."
flask run --host=0.0.0.0 --port=5000
