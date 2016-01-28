Debian Installation
===================

By default, Penates Server 0.5 is only packaged as a standard Python project, downloadable from `Pypi <https://pypi.python.org>`_.
However, you can create pure Debian packages with `DjangoFloor <http://django-floor.readthedocs.org/en/latest/packaging.html#debian-ubuntu>`_.

The source code provides several Bash scripts:

    * `deb-debian-8-python3.sh`,
    * `deb-ubuntu-14.04-15.10.sh`.

These scripts are designed to run on basic installation and are split in five steps:

    * update system and install missing packages,
    * create a virtualenv and install all dependencies,
    * package all dependencies,
    * package Penates Server 0.5,
    * install all packages and Penates Server 0.5, prepare a simple configuration to test.

If everything is ok, you can copy all the .deb packages to your private mirror or to the destination server.
By default, Penates Server 0.5 is installed with Apache 2.4 and systemd.
You can switch to Nginx or supervisor by tweaking the right `stdeb-XXX.cfg` file.


Configuration
-------------

Default configuration file is `/etc/penatesserver/settings.ini`.
If you need more complex settings, you can override default values (given in `djangofloor.defaults` and
`penatesserver.defaults`) by creating a file named `/etc/penatesserver/settings.py`.
After any change in the database configuration or any upgrade, you must migrate the database to create the required tables.

.. code-block:: bash

    sudo -u penatesserver penatesserver-manage migrate


After installation and configuration, do not forget to create a superuser:

.. code-block:: bash

    sudo -u penatesserver penatesserver-manage createsuperuser





Launch the service
------------------

The service can be stopped or started via the `service` command. By default, Penates Server 0.5 is not started.

.. code-block:: bash

    sudo service penatesserver-gunicorn start


If you want Penates Server 0.5 to be started at startup, you have to enable it in systemd:

.. code-block:: bash

    systemctl enable moneta-gunicorn.service




Backup
------

A complete Penates Server 0.5 installation is made a different kinds of files:

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
  cat << EOF > /etc/penatesserver/backup_db.conf
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
  0 1 * * * /usr/local/bin/penatesserver-manage clearsessions
  0 2 * * * logrotate -f /etc/penatesserver/backup_db.conf


Backup of the user-created files can be done with rsync, with a full backup each month:
If you have a lot of files to backup, beware of the available disk place!

.. code-block:: bash

  sudo mkdir -p /var/backups/penatesserver/media
  sudo chown -r penatesserver: /var/backups/penatesserver
  cat << EOF > /etc/penatesserver/backup_media.conf
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
  0 5 0 * * logrotate -f /etc/penatesserver/backup_media.conf

Restoring a backup
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

  cat /var/backups/penatesserver/backup_db.sql.gz | gunzip | /usr/local/bin/penatesserver-manage dbshell
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
  command[penatesserver_gunicorn]=/usr/lib/nagios/plugins/check_procs -C python -a '/usr/local/bin/penatesserver-gunicorn'
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




