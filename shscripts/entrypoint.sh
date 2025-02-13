#!/bin/sh

# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

echo '----------------------hermit ENVIRONMENT VARIABLES------------------------------------'
printenv | grep -E "DATABASE_TSMBSYS_NAME|DATABASE_TSMBSYS_USER|DATABASE_TSMBSYS_PORT|DATABASE_TSMBSYS_PASSWORD|DATABASE_TSMBSYS_HOST|DOCKER_ENV|DJANGO_SECRET_KEY_TSMB_SYS01"
echo '----------------------hermit ENVIRONMENT VARIABLES------------------------------------'

# prep for cron environment variables
printenv | grep -E "DATABASE_TSMBSYS_NAME|DATABASE_TSMBSYS_USER|DATABASE_TSMBSYS_PORT|DATABASE_TSMBSYS_PASSWORD|DATABASE_TSMBSYS_HOST|DOCKER_ENV|DJANGO_SECRET_KEY_TSMB_SYS01" >> /etc/environment
set -a
. /etc/environment
set +a

# # crons
# chmod +x /shscripts/cron_dbbackup.sh
# service cron restart
# # echo '* * * * * echo "hermit3 from container $(date)" >> /var/log/cron.log 2>&1' >> /tmp/mycron
# echo "0 0 * * * /shscripts/cron_dbbackup.sh" >> /tmp/mycron
# # echo "*/5 * * * * /shscripts/cron_dbbackup.sh" >> /tmp/mycron
# # echo '* * * * * echo "hermit4 from container $(date)" >> /var/log/cron.log 2>&1' >> /tmp/mycron
# crontab /tmp/mycron
# service cron restart





# ------------------------------------------------
# Start the Gunicorn server
gunicorn core.wsgi:application --bind 0.0.0.0:8000
# 