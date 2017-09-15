#!/usr/bin/make

tests:
	@nosetests3 -v --with-coverage --cover-package=build_project

clean:
	rm -Rf latest.tar.gz mariadb-data wordpress bitnami-docker-php-fpm
	docker container prune --force
	docker-compose rm --force
	docker image rm php-fpm:5.6.31-r0-custom
