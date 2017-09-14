#!/bin/bash
# init.sh script

# Install WordPress
STOPPED=1
COUNTER=10
TIMEOUT=5
while [ $STOPPED -ne 0 ] && [ $COUNTER -ne 0 ]; do
    COUNTER=`expr $COUNTER - 1`
    sleep $TIMEOUT
    #nc -z mariadb 3306 -w 1
    /opt/bitnami/php/bin/php -r 'mysqli_connect("mariadb", "wordpress", "my-password", null, 3306) or exit(1);'
    STOPPED=$?
    if [ $STOPPED -ne 0 ]; then
    	echo "mariadb: not started yet"
    fi
done

if [ -f /wp_automate.php ]; then
    /opt/bitnami/php/bin/php /wp_automate.php 2> /dev/null
fi

if [ -f /wp_enable_network.php ]; then
    /wp_enable_network.php 2> /dev/null
fi

exec /app-entrypoint.sh "$@"
