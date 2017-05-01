#!/usr/bin/env bash

db_user=siptrack
db_password="siptrack secret."
db_name=siptrack_dev

echo "Starting container"
container_id=$(docker run -e MYSQL_ROOT_PASSWORD="$db_password" -e MYSQL_DATABASE="$db_name" \
    -e MYSQL_USER="$db_user" -e MYSQL_PASSWORD="$db_password" -d mariadb)
container_ip=$(docker inspect -f "{{ .NetworkSettings.IPAddress }}" "$container_id")

echo "DB server IP: $container_ip"

stop_container () {
    echo "Stopping container $container_id"
    docker stop "$container_id"
}

trap stop_container EXIT

export container_ip db_user db_name db_password

echo "Creating config file dev_local.cfg"
envsubst < default_template.cfg > dev_local.cfg

echo "Importing test sql data"
tries=0
while ! mysql -h "$container_ip" -u "$db_user" -p"$db_password" "$db_name" < siptrack_test_data.sql; do
    sleep 3.0
    if [ $tries -ge 10 ]; then
        echo "Failed to import test sql data"
        exit 1
    fi
    ((tries++))
done

echo "Hit Enter to stop container"
read -r junk
