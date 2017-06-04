<b>Dynamic Image processor</b>

<b>Purpose</b>
Given a Image filename with screensize, bandwidth the program generates an optimal image output. 
The image output can be:
a. The output of resized image as Bytes based on bandwidth of network, size requested and screensize
b. The entire image as bytes for a given url passed with content-type as image/jpeg

Primary intent of this program is to embed this and make it imageserver to generate or ouput image files dynamically. It provides capability to resize image when WXH is passed in querystring with option to forcefit the size and return or return the best fit option with no aspect ratio loss.
If you dont want to resize but just optimize for a given screensize of rendering with bandwidth in 2g, 3g etc - it optimizes image quality using Pillow-SIMD and returns the output.

<b>DEPENDENCY </b>

The key dependencies are:
```bash
pip install Pillow-SIMD
pip install logging
pip install configparser
pip install setuptools
pip install mod_wsgi
```
Outside of the above, we have used Flask microframework. It is done to ensure the entire management of base errorhandling, threading of servers are offloaded.
```bash
pip install flask
```

Post above, goto httpd.conf in apache and enable for mod_cgi.so. The best way to find the httpd.conf is to run mod_wsgi-express module-config. Copy all the three lines as given 

```bash
LoadFile "/Users/vph/anaconda/lib/libpython3.6m.dylib"
LoadModule wsgi_module "/Users/vph/anaconda/lib/python3.6/site-packages/mod_wsgi-4.5.16-py3.6-macosx-10.7-x86_64.egg/mod_wsgi/server/mod_wsgi-py36.cpython-36m-darwin.so"
WSGIPythonHome "/Users/vph/anaconda"
```
Note the order in which the above is to be copied. Copy Loadmodule in httpd.conf in the same section as LoadModule seen. Copy the WSGIPythonHome below or after ServerName section in httpd.conf

Copy the files from this project into a folder e.g. /var/www/imgprocessor. It is important that you execute a command to create default log file in case you dont have root or sudo access. Hence execute the following touch commands to generate default log files

```bash
touch imghandler.log
touch dynamicimgprocessor.log
```

In the code files of imgprocessor.py and imghandler.py - change the log path appropriately. In future release, I will try to get this from configuration.
Currently, path used is /var/www/imgprocessor/

Also note the imgprocessor.wsgi which will load the python app running on flask framework. 

In case of my mac, I have created the httpd-vhosts.conf

```bash
<VirtualHost *:80>
    ServerAdmin vishnu@gmail.com
    ServerName dynamicimgprocessor.com
    WSGIDaemonProcess imgprocessor user=vph home=/var/www/imgprocessor threads=40
    WSGIScriptAlias /images /var/www/imgprocessor/imgprocessor.wsgi
    ErrorLog "/private/var/log/apache2/image_error_log"
    CustomLog "/private/var/log/apache2/image_custom_log" common
    <Directory "/var/www/imgprocessor">
        WSGIProcessGroup dynamicimgprocessor
        WSGIScriptReloading On
        Options +ExecCGI
        Order allow,deny
        Allow from all
        Require all granted
    </Directory>
</VirtualHost>

```

Important to note a few items above:
In case of apache 2.4 - need require all granted, in case of apache 2.2 - need order allow,deny and allow from all section.
WSGIScriptReloading is set to on so that any changes to WSGI can happen without restart of apache
WSGIScriptAlias as you can see is pointing to /images. Very important to note that it doesnt have a closing backslash which if added would create issues like REDIRECT etc as WSGI script will keep going in loop
WSGIDaemonProcess has more options like processes and threads etc. Very important to use this for optimizing your threads and processes for performance.Note also the user with which we are running which is vph in this case.

Outside of the log files of application, we also go the apache common log and errorlog configured as given above which you can change as required.

Post the above run the command to provide access/ownership to the running process in the /var/www/imgprocessor/

```bash
cd /var/www/imgprocessor
sudo chown -R vph *.*
sudo chmod 755 *.*
```





