#!/usr/bin/make

tests:
	@nosetests3 -v --with-coverage --cover-package=build_project

clean:
	rm -Rf latest.tar.gz mariadb-data wordpress
	docker container prune --force
	docker-compose rm --force
