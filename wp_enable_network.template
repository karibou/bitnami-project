#!/bin/bash

curl -X POST -F '_wpnonce="deadbeef"' \
	     -F '_wp_http_referer="/wp-admin/network.php"' \
	     -F 'subdomain_install="1"' \
	     -F 'sitename="My Bitnami Project Sites"' \
	     -F 'email="root@localhost"' \
	     -F 'submit="Install"' \
	     http://apache/wp-admin/network.php
