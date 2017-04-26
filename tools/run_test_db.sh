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
    docker stop "$container_id"
}

trap stop_container EXIT

sleep 4

export container_ip db_user db_name db_password

echo "Creating config file dev_local.cfg"
envsubst < default_template.cfg > dev_local.cfg

echo "Importing test sql data"
mysql -u "$db_user" -p"$db_password" < siptrack_test_data.sql

echo "Hit Enter to stop container"
read -r junk
