# bitnami-project

# Pre-requisite

The project has been realized using an up-to-date Ubuntu 17.04 Zesty distribution. The latest upstream packages for Docker were used.

## Native ubuntu Packages
The following Ubuntu native packages will be required in order for the build_project script to complete correctly :
  * python3-pip firefox

(Firefox may be used for testing)

The following packages are required in order to to run the unittests
  * python3-nose
  * python3-coverage
The following command may be used to install them :
```
$ sudo apt install python3-pip python3-nose python3-coverage firefox
```
## Docker CE Installation
The docker version used for the project is the latest Docker CE. To install the latest version follow the instructions from https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/
```
$ sudo apt-get install \
apt-transport-https \
ca-certificates \
curl \
software-properties-common
$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
$ sudo add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) \
    stable"
$ sudo apt-get update
$ sudo apt-get install docker-ce
$ sudo adduser ubuntu docker
$ exit
```
And log back in to gain the docker group

## docker-compose installation
```
sudo -i
$ curl -L https://github.com/docker/compose/releases/download/1.15.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
$ chmod 755 /usr/local/bin/docker-compose
exit
```
## Python modules
The docker API and jinja2 are needed by the build_project script. They are installed using pip3:

  * Docker API :
```
$ sudo pip3 install docker
```
  * Jinja2 :
```
$ sudo pip3 install jinja2
```
## wordpress.example.com hostname definition
In order to reach your wordpress service, you will need to add the wordpress.example.com host to your /etc/hosts file:
```
$ echo "127.0.0.1       wordpress.example.com" | sudo tee -a /etc/hosts
```
# Get the project

## Using the tarball

Extract the tarball using tar :
```
$ tar xf bitnami_project.tgz
```

## Using GIT
```
git clone https://github.com/karibou/bitnami-project.git
cd bitnami_project
```

# Build the project
Just run the build_project script
```
$ ./build_project.py
Downloading new latest.tar.gz
We have the latest latest.tar.gz...Done.
Extracting new tarball...Done.
Setting up source tree permissions...Done.
Custom files setup...Done.
Cloning bitnamis php-fpm image repository
Building new docker custom php-fpm image...Done
Project creation completed
Use the following command to start the service :
    docker-compose up

You can connect to wordpress with :
   username : hello
   password : world
```

# Run the project

As outlined in the output of the build_project.py command, you only have to run *docker-compose up* command to start the wordpress service

## Customize the wordpress service

The two variables *MARIADB_WP_USER* and *MARIADB_WP_PASSWORD* may be used to define specific username and password. The default username and password will be wordpress/wordpress if those are not defined.

The other *MARIADB_* variables can also be changed to fit user needs.

# Theory of operation

The *build_project.py* script starts by getting the latest tarball from the official Wordpress website. If a *latest.tar.gz* file is present, the MD5 hash will be checked to confirm that it is indeed the latest.

If no file is present, it will download it from the web and verify that the MD5 checksum matches. If it matches, the script will extract the tarball locally.

The Docker API is then used to setup the wordpress files group id correctly.

Template files are used for the wp-config.php and the wp_automate.php scripts as they rely on the *MARIADB_* variables definitions present in the *docker-compose.yml* file. Those two files are rendered from their templates. *wp-config.php* is placed in the wordpress sub-directory where it will later be used.

At this point, we clone the Bitnami php-fpm image repository, starting from a fresh new one if one already exists. A custom-made *php-fpm_entrypoint.sh* script is copied at the top of the rootfs directory along with the *wp_automate.php* script generated earlier. Only version 5.6 of the image is handled by the script.

php-fpm_entrypoint.sh will loop trying to establish a mysql connection to the database for up to 60 seconds. Once a connection is established, it will run the wp_automate.php script to setup the wordpress instance with the necessary information so the instance is ready to be used. It terminates by calling the existing */app-entrypoint.sh* script as it would normally would.

The Dockerfile in Bitnami's repository is modified to use the custom-made *php-fpm_entrypoint.sh*. We also fetch the full image version from the file in order to correctly name the image that we will produce. We complete this phase by using the Docker API to create a new image locally. This local image will be used to launch the docker service. The image name will be appended with a *-custom* on the image tag to separate it from the official image.

The script terminates by displaying the command to be run to start the Docker service along with the credentials to be used to log into wordpress.

# Alternate build method
The method cited above was chosen since the project's description clearly outlined the repository cloning and Dockerfile modification steps. But an alternate method was also tested prior to completing the project.

It is possible to use only the docker-compose syntax to achieve the same result without having to create a customized version of Bitnami's php-fpm image.

The two *php-fpm_entrypoint.sh* and *wp_automate.php* scripts can be made available as volumes and called from within the container using *entrypoint* and *command* overrides in the docker-compose.yml file. Using this method, the service can be brought up with the pristine php-fpm image.

A version of this solution can be tested using the docker-compose-alternate.yml file. The steps are :
```
$ cp docker-compose.yml docker-compose.ref
$ cp docker-compose-alternate.yml docker-compose.yml
$ ./build_project.ph -a
$ docker-compose up

```
# Project notes

 * The script in *Hint #1* make use of the netcat command (nc) which is not available on the Bitnami images. We reverted to use mysql to test the database connection so maybe the example should be fixed.
