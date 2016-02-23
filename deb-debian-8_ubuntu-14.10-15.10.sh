#!/bin/bash
set -e

# base packages
sudo apt-get update
sudo apt-get upgrade --yes
sudo apt-get install --yes vim dh-make ntp rsync liblzma-dev tree
sudo apt-get install --yes python-all-dev virtualenvwrapper \
    python-tz python-setuptools \
    python-oauthlib \
    apache2 libapr1 libaprutil1 libaprutil1-dbd-sqlite3 libaprutil1-ldap \
    python-medusa python-meld3 ssl-cert python-msgpack
sudo apt-get install --yes python-ldap libldap2-dev libsasl2-dev python-markdown\
 python-pygments python-netaddr python-jinja2 gunicorn python-futures python-gunicorn
source /etc/bash_completion.d/virtualenvwrapper



# create the virtual env
set +e
mkvirtualenv -p `which python` djangofloor
workon djangofloor
pip install setuptools --upgrade
pip install pip --upgrade
pip install debtools djangofloor
set -e
python setup.py install



# generate packages for all dependencies
multideb -r -v -x stdeb-debian-8_ubuntu-14.10-15.10.cfg

# creating package for penatesserver
rm -rf `find * | grep pyc$`
python setup.py bdist_deb_django -x stdeb-debian-8_ubuntu-14.10-15.10.cfg
deb-dep-tree deb_dist/*deb
mv deb_dist/*deb deb



# install all packages
sudo dpkg -i deb/python-*.deb

# package configuration
IP=`/sbin/ifconfig | grep -Eo 'inet (addr:|adr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -n 1`
sudo sed -i "s/localhost/$IP/g" /etc/apache2/sites-available/penatesserver.conf
sudo sed -i "s/localhost/$IP/g" /etc/penatesserver/settings.ini
sudo a2ensite penatesserver.conf
sudo a2dissite 000-default.conf
sudo -u penatesserver penatesserver-manage migrate
sudo service penatesserver-gunicorn start
sudo service apache2 restart

wget http://$IP/
set -e
