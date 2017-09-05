# bitnami-project

#Pre-requisite

##Native ubuntu Packages
The following Ubuntu native packages will be required in order for the build_project script to complete correctly :
  * python3-pip

##Docker CE Installation
The docker version used for the project is the latest Docker CE. To install the latest version follow the instructions from https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/
```$ sudo apt-get install \
```    apt-transport-https \
```    ca-certificates \
```    curl \
```    software-properties-common
```$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
```$ sudo add-apt-repository \
```$    "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
```$    $(lsb_release -cs) \
```$    stable"
```$ sudo apt-get update
```$ sudo apt-get install docker-ce
```$ sudo adduser ubuntu docker
```$ exit
And log back in to gain the docker group

The following packages are required in order to to run the unittests
  * python3-nose
  * python3-coverage
The following command may be used to install them :
```sudo apt install python3-pip python3-nose python3-coverage

##Python modules
The docker API and jinja2 are needed by the build_project script. They are installed using pip3:

Docker API :
    pip3 install docker
Jinja2 :
```pip3 install jinja2

# Get the project

##Using the tarball

Extract the tarball using tar :
``` tar xf bitnami_project.tgz
``` cd bitnami_project

##Using GIT
```git clone https://github.com/karibou/bitnami-project.git
```cd bitnami_project
