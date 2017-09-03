#!/usr/bin/make

tests:
	@nosetests3 -v --with-coverage --cover-package=build_project
