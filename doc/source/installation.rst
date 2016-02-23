Installation
============

Like many Python packages, you can use several methods to install Penates Server.
Penates Server designed to run with python2.7.x.
The following packages are also required:

  * setuptools >= 3.0
  * djangofloor >= 0.18.0
  * python-gnupg
  * rubymarshal
  * pyyaml



Of course you can install it from the source, but the preferred way is to install it as a standard Python package, via pip.


Installing or Upgrading
-----------------------

Here is a simple tutorial to install Penates Server on a basic Debian/Linux installation.
You should easily adapt it on a different Linux or Unix flavor.

Ruby
----

If you want to use the Ruby mirror functionnality, Ruby is required on the server:

.. code-block:: bash

   sudo apt-get install ruby


Database
--------

PostgreSQL is often a good choice for Django sites:

.. code-block:: bash

   sudo apt-get install postgresql
   echo "CREATE USER penatesserver" | sudo -u postgres psql -d postgres
   echo "ALTER USER penatesserver WITH ENCRYPTED PASSWORD '5trongp4ssw0rd'" | sudo -u postgres psql -d postgres
   echo "ALTER ROLE penatesserver CREATEDB" | sudo -u postgres psql -d postgres
   echo "CREATE DATABASE penatesserver OWNER penatesserver" | sudo -u postgres psql -d postgres




Apache
------

I only present the installation with Apache, but an installation behind nginx should be similar.
You cannot use different server names for browsing your mirror. If you use `penatesserver.example.org`
in the configuration, you cannot use its IP address to access the website.

.. code-block:: bash

    SERVICE_NAME=penatesserver.example.org
    sudo apt-get install apache2 libapache2-mod-xsendfile
    sudo a2enmod headers proxy proxy_http
    sudo a2dissite 000-default.conf
    # sudo a2dissite 000-default on Debian7
    cat << EOF | sudo tee /etc/apache2/sites-available/penatesserver.conf
    <VirtualHost *:80>
        ServerName $SERVICE_NAME
        Alias /static/ ./django_data/static/
        ProxyPass /static/ !
        <Location /static/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
        ProxyPass / http://127.0.0.1:9000/
        ProxyPassReverse / http://127.0.0.1:9000/
        DocumentRoot ./django_data/static
        ServerSignature off
        XSendFile on
        XSendFilePath ./django_data/data/media
        # in older versions of XSendFile (<= 0.9), use XSendFileAllowAbove On
    </VirtualHost>
    EOF
    sudo mkdir ./django_data
    sudo chown -R www-data:www-data ./django_data
    sudo a2ensite penatesserver.conf
    sudo apachectl -t
    sudo apachectl restart


If you want to use SSL:

.. code-block:: bash

    sudo apt-get install apache2 libapache2-mod-xsendfile
    PEM=/etc/apache2/`hostname -f`.pem
    # ok, I assume that you already have your certificate
    sudo a2enmod headers proxy proxy_http ssl
    openssl x509 -text -noout < $PEM
    sudo chown www-data $PEM
    sudo chmod 0400 $PEM

    sudo apt-get install libapache2-mod-auth-kerb
    KEYTAB=/etc/apache2/http.`hostname -f`.keytab
    # ok, I assume that you already have your keytab
    sudo a2enmod auth_kerb
    cat << EOF | sudo ktutil
    rkt $KEYTAB
    list
    quit
    EOF
    sudo chown www-data $KEYTAB
    sudo chmod 0400 $KEYTAB

    SERVICE_NAME=penatesserver.example.org
    cat << EOF | sudo tee /etc/apache2/sites-available/penatesserver.conf
    <VirtualHost *:80>
        ServerName $SERVICE_NAME
        RedirectPermanent / https://$SERVICE_NAME/
    </VirtualHost>
    <VirtualHost *:443>
        ServerName $SERVICE_NAME
        SSLCertificateFile $PEM
        SSLEngine on
        Alias /static/ ./django_data/static/
        ProxyPass /static/ !
        <Location /static/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
        ProxyPass / http://127.0.0.1:9000/
        ProxyPassReverse / http://127.0.0.1:9000/
        DocumentRoot ./django_data/static
        ServerSignature off
        RequestHeader set X_FORWARDED_PROTO https
        <Location />
            AuthType Kerberos
            AuthName "Penates Server"
            KrbAuthRealms EXAMPLE.ORG example.org
            Krb5Keytab $KEYTAB
            KrbLocalUserMapping On
            KrbServiceName HTTP
            KrbMethodK5Passwd Off
            KrbMethodNegotiate On
            KrbSaveCredentials On
            Require valid-user
            RequestHeader set REMOTE_USER %{REMOTE_USER}s
        </Location>
        XSendFile on
        XSendFilePath ./django_data/data/media
        # in older versions of XSendFile (<= 0.9), use XSendFileAllowAbove On
        <Location /core/p/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
        <Location /repo/p/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
    </VirtualHost>
    EOF
    sudo mkdir ./django_data
    sudo chown -R www-data:www-data ./django_data
    sudo a2ensite penatesserver.conf
    sudo apachectl -t
    sudo apachectl restart




Application
-----------

Now, it's time to install Penates Server:

.. code-block:: bash

    sudo mkdir -p ./django_data
    sudo adduser --disabled-password penatesserver
    sudo chown penatesserver:www-data ./django_data
    sudo apt-get install virtualenvwrapper python2.7 python2.7-dev build-essential postgresql-client libpq-dev
    # application
    sudo -u penatesserver -i
    mkvirtualenv penatesserver -p `which python2.7`
    workon penatesserver
    pip install setuptools --upgrade
    pip install pip --upgrade
    pip install penatesserver psycopg2 gevent
    mkdir -p $VIRTUAL_ENV/etc/penatesserver
    cat << EOF > $VIRTUAL_ENV/etc/penatesserver/settings.ini
    [database]
    engine = django.db.backends.sqlite3
    host = 
    name = ./django_data/data/database.sqlite3
    password = 
    port = 
    user = 
    [global]
    admin_email = admin@localhost
    bind_address = 127.0.0.1:9000
    data_path = ./django_data
    debug = True
    default_group = Users
    keytab = ./django_data/pki/private/kadmin.keytab
    language_code = fr-fr
    offer_host_keytabs = True
    protocol = http
    remote_user_header = HTTP_REMOTE_USER
    secret_key = cLc7rCD75uO6uFVr6ojn6AYTm2DGT2t7hb7OH5Capk29kcdy7H
    server_name = localhost
    time_zone = Europe/Paris
    [ldap]
    base_dn = dc=test,dc=example,dc=org
    name = ldap://192.168.56.101/
    password = toto
    user = cn=admin,dc=test,dc=example,dc=org
    [penates]
    country = FR
    domain = test.example.org
    email_address = admin@test.example.org
    locality = Paris
    organization = example.org
    realm = EXAMPLE.ORG
    state = Ile-de-France
    subnets = 10.19.1.0/24,10.19.1.1
    10.8.0.0/16,10.8.0.1
    [powerdns]
    engine = django.db.backends.sqlite3
    host = localhost
    name = ./django_data/data/pdns.sqlite3
    password = toto
    port = 5432
    user = powerdns
    EOF
    chmod 0400 $VIRTUAL_ENV/etc/penatesserver/settings.ini
    # required since there are password in this file
    penatesserver-manage migrate
    penatesserver-manage collectstatic --noinput
    moneta-manage createsuperuser
    chmod 0700 /var/moneta/gpg
    moneta-manage gpg_gen generate --no-existing-keys
    KEY_ID=`moneta-manage gpg_gen show --only-id | tail -n 1`
    sed -i "s//$KEY_ID/" $VIRTUAL_ENV/etc/moneta/settings.ini

On VirtualBox, you may need to install rng-tools to generate enough entropy for GPG keys:

.. code-block:: bash

    sudo apt-get install rng-tools
    echo "HRNGDEVICE=/dev/urandom" | sudo tee -a /etc/default/rng-tools
    sudo /etc/init.d/rng-tools restart



supervisor
----------

Supervisor is required to automatically launch penatesserver:

.. code-block:: bash


    sudo apt-get install supervisor
    cat << EOF | sudo tee /etc/supervisor/conf.d/penatesserver.conf
    [program:penatesserver_gunicorn]
    command = /home/penatesserver/.virtualenvs/penatesserver/bin/penatesserver-gunicorn
    user = penatesserver
    EOF
    sudo service supervisor stop
    sudo service supervisor start

Now, Supervisor should start penatesserver after a reboot.


systemd
-------

You can also use systemd to launch penatesserver:

.. code-block:: bash

    cat << EOF | sudo tee /etc/systemd/system/penatesserver-gunicorn.service
    [Unit]
    Description=Penates Server Gunicorn process
    After=network.target
    [Service]
    User=penatesserver
    Group=penatesserver
    WorkingDirectory=./django_data/
    ExecStart=/home/penatesserver/.virtualenvs/penatesserver/bin/penatesserver-gunicorn
    ExecReload=/bin/kill -s HUP $MAINPID
    ExecStop=/bin/kill -s TERM $MAINPID
    [Install]
    WantedBy=multi-user.target
    EOF
    systemctl enable penatesserver-gunicorn.service
    sudo service penatesserver-gunicorn start



