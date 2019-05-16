q#!/usr/bin/bash

if ! [ -f /usr/bin/pacman ]; then
    printf "[!] Need \"pacman\" to continue (Is this ArchLinux?), quitting!\n"
    exit 1
fi

pacman --noconfirm -S archlinux-keyring
pacman --noconfirm -Syu apache python-django python-virtualenv mod_wsgi mariadb git

mkdir -p /opt/scorebot/db
mkdir -p /opt/scorebot/sbe
mkdir -p /opt/scorebot/httpd
mkdir -p /opt/scorebot/python
mkdir -p /opt/scorebot/storage

rm -rf /var/lib/mysql 2> /dev/null
rm -rf /etc/httpd/conf/extra 2> /dev/null
rm -rf /etc/httpd/conf/httpd.conf 2> /dev/null

virtualenv --always-copy --clear -q /opt/scorebot/python
PYTHON_ENV=""
for py in $(find /opt/scorebot/python/lib/ -type d -name python*); do
    if [ -d "$py" ]; then
        PYTHON_ENV="$py"
    fi
done

cat <<EOF> /opt/scorebot/httpd/httpd.conf
ServerRoot "/etc/httpd"
Listen 80
LoadModule wsgi_module modules/mod_wsgi.so
LoadModule authz_host_module modules/mod_authz_host.so
LoadModule authz_core_module modules/mod_authz_core.so
LoadModule access_compat_module modules/mod_access_compat.so
LoadModule socache_shmcb_module modules/mod_socache_shmcb.so
LoadModule reqtimeout_module modules/mod_reqtimeout.so
LoadModule mime_module modules/mod_mime.so
LoadModule http2_module modules/mod_http2.so
LoadModule log_config_module modules/mod_log_config.so
LoadModule env_module modules/mod_env.so
LoadModule headers_module modules/mod_headers.so
LoadModule setenvif_module modules/mod_setenvif.so
LoadModule mpm_prefork_module modules/mod_mpm_prefork.so
LoadModule unixd_module modules/mod_unixd.so
LoadModule vhost_alias_module modules/mod_vhost_alias.so
LoadModule negotiation_module modules/mod_negotiation.so
LoadModule dir_module modules/mod_dir.so
LoadModule alias_module modules/mod_alias.so
LoadModule rewrite_module modules/mod_rewrite.so
<IfModule unixd_module>
User http
Group http
</IfModule>
<Directory /srv/http/>
   AllowOverride none
   Require all granted
</Directory>
DocumentRoot "/srv/http"
<IfModule dir_module>
    DirectoryIndex index.html
</IfModule>
<Files ".ht*">
    Require all denied
</Files>
ErrorLog "/var/log/httpd/error_log"
LogLevel warn
<IfModule log_config_module>
    LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" combined
    LogFormat "%h %l %u %t \"%r\" %>s %b" common
    <IfModule logio_module>
      LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" %I %O" combinedio
    </IfModule>
    CustomLog "/var/log/httpd/access_log" common
</IfModule>
<Directory "/srv/http/cgi-bin">
    AllowOverride None
    Options None
    Require all denied
</Directory>
<IfModule mime_module>
    TypesConfig conf/mime.types
    AddType application/x-compress .Z
    AddType application/x-gzip .gz .tgz
</IfModule>
<Directory />
    AllowOverride none
    Require all denied
    ErrorDocument 500 "Server Error!"
</Directory>
ErrorDocument 500 "Server Error!"
Include /opt/scorebot/httpd/httpd-mpm.conf
Include /opt/scorebot/httpd/httpd-default.conf
Include /opt/scorebot/httpd/httpd-languages.conf
Include /opt/scorebot/httpd/httpd-scorebot-sbe.conf
TraceEnable off
Header always set X-Frame-Options SAMEORIGIN
Header always set X-Content-Type-Options nosniff
Header always set X-XSS-Protection "1; mode=block"
FileETag None
EOF
cat <<EOF> /opt/scorebot/httpd/httpd-mpm.conf
<IfModule !mpm_netware_module>
    PidFile "/run/httpd/httpd.pid"
</IfModule>
<IfModule mpm_prefork_module>
    StartServers             5
    MinSpareServers          5
    MaxSpareServers         10
    MaxRequestWorkers      250
    MaxConnectionsPerChild   0
</IfModule>
<IfModule mpm_worker_module>
    StartServers             3
    MinSpareThreads         75
    MaxSpareThreads        250
    ThreadsPerChild         25
    MaxRequestWorkers      400
    MaxConnectionsPerChild   0
</IfModule>
<IfModule mpm_event_module>
    StartServers             3
    MinSpareThreads         75
    MaxSpareThreads        250
    ThreadsPerChild         25
    MaxRequestWorkers      400
    MaxConnectionsPerChild   0
</IfModule>
<IfModule mpm_netware_module>
    ThreadStackSize      65536
    StartThreads           250
    MinSpareThreads         25
    MaxSpareThreads        250
    MaxThreads            1000
    MaxConnectionsPerChild   0
</IfModule>
<IfModule mpm_mpmt_os2_module>
    StartServers             2
    MinSpareThreads          5
    MaxSpareThreads         10
    MaxConnectionsPerChild   0
</IfModule>
<IfModule mpm_winnt_module>
    ThreadsPerChild        150
    MaxConnectionsPerChild   0
</IfModule>
<IfModule !mpm_netware_module>
    MaxMemFree            2048
</IfModule>
<IfModule mpm_netware_module>
    MaxMemFree             100
</IfModule>
EOF
cat <<EOF> /opt/scorebot/httpd/httpd-default.conf
Timeout 60
KeepAlive On
MaxKeepAliveRequests 100
KeepAliveTimeout 5
UseCanonicalName Off
AccessFileName .htaccess
ServerTokens Prod
ServerSignature Off
HostnameLookups Off
<IfModule reqtimeout_module>
  RequestReadTimeout header=20-40,MinRate=500 body=20,MinRate=500
</IfModule>
EOF
cat <<EOF> /opt/scorebot/httpd/httpd-languages.conf
DefaultLanguage en
AddLanguage ca .ca
AddLanguage cs .cz .cs
AddLanguage da .dk
AddLanguage de .de
AddLanguage el .el
AddLanguage en .en
AddLanguage eo .eo
AddLanguage es .es
AddLanguage et .et
AddLanguage fr .fr
AddLanguage he .he
AddLanguage hr .hr
AddLanguage it .it
AddLanguage ja .ja
AddLanguage ko .ko
AddLanguage ltz .ltz
AddLanguage nl .nl
AddLanguage nn .nn
AddLanguage no .no
AddLanguage pl .po
AddLanguage pt .pt
AddLanguage pt-BR .pt-br
AddLanguage ru .ru
AddLanguage sv .sv
AddLanguage tr .tr
AddLanguage zh-CN .zh-cn
AddLanguage zh-TW .zh-tw
LanguagePriority en ca cs da de el eo es et fr he hr it ja ko ltz nl nn no pl pt pt-BR ru sv tr zh-CN zh-TW
ForceLanguagePriority Prefer Fallback
AddCharset us-ascii.ascii .us-ascii
AddCharset ISO-8859-1  .iso8859-1  .latin1
AddCharset ISO-8859-2  .iso8859-2  .latin2 .cen
AddCharset ISO-8859-3  .iso8859-3  .latin3
AddCharset ISO-8859-4  .iso8859-4  .latin4
AddCharset ISO-8859-5  .iso8859-5  .cyr .iso-ru
AddCharset ISO-8859-6  .iso8859-6  .arb .arabic
AddCharset ISO-8859-7  .iso8859-7  .grk .greek
AddCharset ISO-8859-8  .iso8859-8  .heb .hebrew
AddCharset ISO-8859-9  .iso8859-9  .latin5 .trk
AddCharset ISO-8859-10  .iso8859-10  .latin6
AddCharset ISO-8859-13  .iso8859-13
AddCharset ISO-8859-14  .iso8859-14  .latin8
AddCharset ISO-8859-15  .iso8859-15  .latin9
AddCharset ISO-8859-16  .iso8859-16  .latin10
AddCharset ISO-2022-JP .iso2022-jp .jis
AddCharset ISO-2022-KR .iso2022-kr .kis
AddCharset ISO-2022-CN .iso2022-cn .cis
AddCharset Big5.Big5   .big5 .b5
AddCharset cn-Big5 .cn-big5
AddCharset WINDOWS-1251 .cp-1251   .win-1251
AddCharset CP866   .cp866
AddCharset KOI8  .koi8
AddCharset KOI8-E  .koi8-e
AddCharset KOI8-r  .koi8-r .koi8-ru
AddCharset KOI8-U  .koi8-u
AddCharset KOI8-ru .koi8-uk .ua
AddCharset ISO-10646-UCS-2 .ucs2
AddCharset ISO-10646-UCS-4 .ucs4
AddCharset UTF-7   .utf7
AddCharset UTF-8   .utf8
AddCharset UTF-16  .utf16
AddCharset UTF-16BE .utf16be
AddCharset UTF-16LE .utf16le
AddCharset UTF-32  .utf32
AddCharset UTF-32BE .utf32be
AddCharset UTF-32LE .utf32le
AddCharset euc-cn  .euc-cn
AddCharset euc-gb  .euc-gb
AddCharset euc-jp  .euc-jp
AddCharset euc-kr  .euc-kr
AddCharset EUC-TW  .euc-tw
AddCharset gb2312  .gb2312 .gb
AddCharset iso-10646-ucs-2 .ucs-2 .iso-10646-ucs-2
AddCharset iso-10646-ucs-4 .ucs-4 .iso-10646-ucs-4
AddCharset shift_jis   .shift_jis .sjis
EOF
cat <<EOF> /opt/scorebot/httpd/httpd-scorebot-sbe.conf
<VirtualHost *:80>
<Location />
    Order allow,deny
    Allow from all
</Location>
<Directory /opt/scorebot/sbe>
    <Files wsgi.py>
	    Require all granted
	</Files>
</Directory>
Alias /upload /opt/scorebot/sbe/storage
<Directory /opt/scorebot/sbe/storage>
    AllowOverride All
	Options FollowSymlinks
	Require all granted
</Directory>
Alias /static /opt/scorebot/sbe/html/assets
<Directory /opt/scorebot/sbe/html/assets>
    AllowOverride All
    Options FollowSymlinks
	Require all granted
</Directory>
WSGIProcessGroup scorebot
WSGIScriptAlias / /opt/scorebot/sbe/scorebot/wsgi.py
WSGIDaemonProcess scorebot python-path=/opt/scorebot/sbe:$PYTHON_ENV/site-packages
</VirtualHost>
EOF

ln -s /opt/scorebot/db /var/lib/mysql
ln -s /opt/scorebot/httpd/httpd.conf /etc/httpd/conf/httpd.conf

git clone https://github.com/iDigitalFlame/scorebot3-core /opt/scorebot/sbe
if [ -d /opt/scorebot/sbe/scorebot_static ]; then
    mkdir -p /opt/scorebot/sbe/html
    mv /opt/scorebot/sbe/scorebot_static /opt/scorebot/sbe/html/assets
fi

mysql_install_db --force --basedir=/usr --datadir=/var/lib/mysql --user=mysql

sed -ie 's/skip-external-locking/skip-external-locking\nbind-address = 127.0.0.1/g' /etc/mysql/my.cnf
rm /etc/mysql/my.cnfe

chmod -R 770 /opt/scorebot/db
chmod -R 550 /opt/scorebot/sbe
chmod -R 550 /opt/scorebot/httpd
chmod -R 550 /opt/scorebot/python
chmod -R 770 /opt/scorebot/storage

chown -R root:http /opt/scorebot
chown -R mysql:mysql /opt/scorebot/db

find /opt/scorebot/sbe -type f -exec chmod 440 {} \;
find /opt/scorebot/httpd -type f -exec chmod 440 {} \;
find /opt/scorebot/python -type f -exec chmod 440 {} \;
find /opt/scorebot/python/bin -type f -exec chmod 550 {} \;

systemctl enable mysqld.service
systemctl start mysqld.service

PASSWORD="Scorebot123!"

printf "\nY\n$PASSWORD\n$PASSWORD\nY\nY\nY\nY\n" | mysql_secure_installation
systemctl restart mysqld.service

systemctl enable httpd.service