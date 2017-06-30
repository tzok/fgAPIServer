# fgtest
The script `fgtest.sh` is bash script that autimatically performs a set of functional tests against a baseline installation of FutureGateway.

## Execution
This script must be executed as super-user with sudo or root and the execution of the `fgtest.sh` script jave to be done inside the fgAPIServer/fgtest directory

```
     # cd /home/futuregateway/fgAPIServer/fgtest
     # ./fgtest.sh
```

The script will perform all defined tests and will create reports as HTML pages under the www directory

## Publishing results
The HTML reports available under the fgtest/www directory can be published by any web server below configurations are appliable under apache

```
# cat >/etc/apache2/sites-available/fgtest.conf <<EOF
Alias /fgtest /home/futuregateway/fgAPIServer/fgtest/www
<Directory /home/futuregateway/fgAPIServer/fgtest/www>
  Order deny,allow
  Allow from all
  Options All
  AllowOverride All
  Require all granted
</Directory>
EOF
```

After inserting the new httpd endpoint; restart apache

## Pre-requisites
    jquery
```
      # wget https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js -O www/js/jquery.min.js
```
    bootstrap:
```
      # wget https://github.com/twbs/bootstrap/releases/download/v3.3.7/bootstrap-3.3.7-dist.zip
      # unzip bootstrap-3.3.7-dist.zip
      # cd www/css
      # ln -s ../../bootstrap-3.3.7-dist/css/bootstrap-theme.min.css bootstrap-theme.min.css
      # ln -s ../../bootstrap-3.3.7-dist/css/bootstrap-theme.min.css.map bootstrap-theme.min.css.map
      # ln -s ../../bootstrap-3.3.7-dist/css/bootstrap.min.css bootstrap.min.css
      # cd ../fonts
      # ln -s ../../bootstrap-3.3.7-dist/fonts/ fonts
      # cd ../js
      # ln -s ../../bootstrap-3.3.7-dist/js/bootstrap.min.js bootstrap.min.js 
 ```
    sshpass:
```
      sudo apt-get install sshpass (ubuntu)
      yum install sshpass (yum based)
      dnf install sshpass (fedora)
```


