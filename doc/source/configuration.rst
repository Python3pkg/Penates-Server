
Complete configuration
======================


Configuration options
---------------------

You can look current settings with the following command:

.. code-block:: bash

    penatesserver-manage config

Here is the complete list of settings:

.. code-block:: ini

  [database]
  engine = django.db.backends.sqlite3
  # SQL database engine, can be 'django.db.backends.[postgresql_psycopg2|mysql|sqlite3|oracle]'.
  host = 
  # Empty for localhost through domain sockets or "127.0.0.1" for localhost + TCP
  name = ./django_data/data/database.sqlite3
  # Name of your database, or path to database file if using sqlite3.
  password = 
  # Database password (not used with sqlite3)
  port = 
  # Database port, leave it empty for default (not used with sqlite3)
  user = 
  # Database user (not used with sqlite3)
  [global]
  admin_email = admin@localhost
  # error logs are sent to this e-mail address
  bind_address = 127.0.0.1:9000
  # The socket (IP address:port) to bind to.
  data_path = ./django_data
  # Base path for all data
  debug = False
  # A boolean that turns on/off debug mode.
  default_group = Users
  # Name of the default group for newly-created users.
  keytab = ./django_data/pki/private/kadmin.keytab
  language_code = fr-fr
  # A string representing the language code for this installation.
  offer_host_keytabs = True
  protocol = http
  # Protocol (or scheme) used by your webserver (apache/nginx/…, can be http or https)
  remote_user_header = HTTP_REMOTE_USER
  # HTTP header corresponding to the username when using HTTP authentication.Should be "HTTP_REMOTE_USER". Leave it empty to disable HTTP authentication.
  secret_key = cLc7rCD75uO6uFVr6ojn6AYTm2DGT2t7hb7OH5Capk29kcdy7H
  # A secret key for a particular Django installation. This is used to provide cryptographic signing, and should be set to a unique, unpredictable value.
  server_name = localhost
  # the name of your webserver (should be a DNS name, but can be an IP address)
  time_zone = Europe/Paris
  # A string representing the time zone for this installation, or None. 
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



If you need more complex settings, you can override default values (given in `djangofloor.defaults` and
`penatesserver.defaults`) by creating a file named `/home/penatesserver/.virtualenvs/penatesserver/etc/penatesserver/settings.py`.



Debugging
---------

If something does not work as expected, you can look at logs (in /var/log/supervisor if you use supervisor)
or try to run the server interactively:

.. code-block:: bash

  sudo service supervisor stop
  sudo -u penatesserver -i
  workon penatesserver
  penatesserver-manage config
  penatesserver-manage runserver
  penatesserver-gunicorn




Backup
------

A complete Penates Server installation is made a different kinds of files:

    * the code of your application and its dependencies (you should not have to backup them),
    * static files (as they are provided by the code, you can lost them),
    * configuration files (you can easily recreate it, or you must backup it),
    * database content (you must backup it),
    * user-created files (you must also backup them).

Many backup strategies exist, and you must choose one that fits your needs. We can only propose general-purpose strategies.

We use logrotate to backup the database, with a new file each day.

.. code-block:: bash

  sudo mkdir -p /var/backups/penatesserver
  sudo chown -r penatesserver: /var/backups/penatesserver
  sudo -u penatesserver -i
  cat << EOF > /home/penatesserver/.virtualenvs/penatesserver/etc/penatesserver/backup_db.conf
  /var/backups/penatesserver/backup_db.sql.gz {
    daily
    rotate 20
    nocompress
    missingok
    create 640 penatesserver penatesserver
    postrotate
    myproject-manage dumpdb | gzip > /var/backups/penatesserver/backup_db.sql.gz
    endscript
  }
  EOF
  touch /var/backups/penatesserver/backup_db.sql.gz
  crontab -e
  MAILTO=admin@localhost
  0 1 * * * /home/penatesserver/.virtualenvs/penatesserver/bin/penatesserver-manage clearsessions
  0 2 * * * logrotate -f /home/penatesserver/.virtualenvs/penatesserver/etc/penatesserver/backup_db.conf


Backup of the user-created files can be done with rsync, with a full backup each month:
If you have a lot of files to backup, beware of the available disk place!

.. code-block:: bash

  sudo mkdir -p /var/backups/penatesserver/media
  sudo chown -r penatesserver: /var/backups/penatesserver
  cat << EOF > /home/penatesserver/.virtualenvs/penatesserver/etc/penatesserver/backup_media.conf
  /var/backups/penatesserver/backup_media.tar.gz {
    monthly
    rotate 6
    nocompress
    missingok
    create 640 penatesserver penatesserver
    postrotate
    tar -C /var/backups/penatesserver/media/ -czf /var/backups/penatesserver/backup_media.tar.gz .
    endscript
  }
  EOF
  touch /var/backups/penatesserver/backup_media.tar.gz
  crontab -e
  MAILTO=admin@localhost
  0 3 * * * rsync -arltDE ./django_data/data/media/ /var/backups/penatesserver/media/
  0 5 0 * * logrotate -f /home/penatesserver/.virtualenvs/penatesserver/etc/penatesserver/backup_media.conf

Restoring a backup
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

  cat /var/backups/penatesserver/backup_db.sql.gz | gunzip | /home/penatesserver/.virtualenvs/penatesserver/bin/penatesserver-manage dbshell
  tar -C ./django_data/data/media/ -xf /var/backups/penatesserver/backup_media.tar.gz





Monitoring
----------


Nagios or Shinken
~~~~~~~~~~~~~~~~~

You can use Nagios checks to monitor several points:

  * connection to the application server (gunicorn or uwsgi):
  * connection to the database servers (PostgreSQL),
  * connection to the reverse-proxy server (apache or nginx),
  * the validity of the SSL certificate (can be combined with the previous check),
  * creation date of the last backup (database and files),
  * living processes for gunicorn, postgresql, apache,
  * standard checks for RAM, disk, swap…

Here is a sample NRPE configuration file:

.. code-block:: bash

  cat << EOF | sudo tee /etc/nagios/nrpe.d/penatesserver.cfg
  command[penatesserver_wsgi]=/usr/lib/nagios/plugins/check_http -H 127.0.0.1 -p 9000
  command[penatesserver_reverse_proxy]=/usr/lib/nagios/plugins/check_http -H localhost -p 80 -e 401
  command[penatesserver_backup_db]=/usr/lib/nagios/plugins/check_file_age -w 172800 -c 432000 /var/backups/penatesserver/backup_db.sql.gz
  command[penatesserver_backup_media]=/usr/lib/nagios/plugins/check_file_age -w 3024000 -c 6048000 /var/backups/penatesserver/backup_media.sql.gz
  command[penatesserver_gunicorn]=/usr/lib/nagios/plugins/check_procs -C python -a '/home/penatesserver/.virtualenvs/penatesserver/bin/penatesserver-gunicorn'
  EOF

Sentry
~~~~~~

For using Sentry to log errors, you must add `raven.contrib.django.raven_compat` to the installed apps.

.. code-block:: ini

  [global]
  extra_apps = raven.contrib.django.raven_compat
  [sentry]
  dsn_url = https://[key]:[secret]@app.getsentry.com/[project]

Of course, the Sentry client (Raven) must be separately installed, before testing the installation:

.. code-block:: bash

  sudo -u penatesserver -i
  penatesserver-manage raven test





LDAP groups
-----------

There are two possibilities to use LDAP groups, with their own pros and cons:

  * on each request, use an extra LDAP connection to retrieve groups instead of looking in the SQL database,
  * regularly synchronize groups between the LDAP server and the SQL servers.

The second approach can be used without any modification in your code and remove a point of failure
in the global architecture (if you allow some delay during the synchronization process).
A tool exists for such synchronization: `MultiSync <https://github.com/d9pouces/Multisync>`_.
