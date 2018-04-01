# put.io-aria2c-downloader
Python script that sends put.io files to aria2c for download


## Install
This setup assumes you have aria2c running with rpc running. Also assumes ssl enabled
```bash
mkdir /opt/put.io
cd /opt/put.io
git clone https://github.com/cvockrodt/put.io-aria2c-downloader.git
```

### Configuration
Copy the example configuration file where you want it
```bash 
mkdir /var/opt/put.io 
cp /opt/put.io/config.ini.example /var/opt/put.io/config.ini
```
Edit the configuration with watch folders, put.io token and aria2c secret token, aria2c rpc url, etc.
```bash
vi /var/opt/put.io/config.ini
``` 


### crontab
```crontab
*/5 * * * * /bin/bash /opt/put.io/is_putio_downloader_running >> /var/opt/put.io/putio.log 2>&1
```
