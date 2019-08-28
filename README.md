[![Build Status](https://travis-ci.org/cvockrodt/put.io-aria2c-downloader.svg?branch=master)](https://travis-ci.org/cvockrodt/put.io-aria2c-downloader)

# put.io-aria2c-downloader
Python script that sends put.io download links to aria2c for download


## Install
This setup assumes you have aria2c up with rpc running
```bash
pip install putio-downloader
```

## Usage
```
Usage: putio-download [OPTIONS]

  CLI entrypoint for put.io downloader

Options:
  --oauth-token TEXT          [required]
  --keep-folder-structure
  --root-watch-dir INTEGER    [required]
  --aria2c-secret-token TEXT  [required]
  --root-download-dir TEXT    [required]
  --post-process-dir TEXT     [required]
  --watch-folders TEXT        [required]
  --rpc-url TEXT              [required]
  --version
  -q, --quiet
  -v, --verbose
  --config FILE               Read configuration from PATH.
  --help                      Show this message and exit.
```

### Configuration
If you don't want to pass those options on the command line, you can work with a config file to pass all or just some of the following:
```
oauth_token = 'XXXXXXXX'
keep_folder_structure = 'true'
root_watch_dir = 0
root_download_dir = '/download/incomplete'
aria2c_secret_token = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
post_process_dir = '/download/complete'
rpc_url = 'https://example.com:6800/rpc'
watch_folders = ['isos', 'news', 'videos']
```

For windows, directories must follow windows' directory formatting, ie.
```
root_download_dir = 'C:\\download\\incomplete'
post_process_dir = 'C:\\download\\complete'
```

### crontab
Run the download script on an interval so you don't miss out on any of your files
```crontab
*/10 * * * * putio-download --config ~/myconfig.ini >> ~/putio.log 2>&1
```

To prevent multiple instances of putio-download from running, consider using a wrapper script like the following:
```bash
#!/bin/bash
COUNT=`ps -ef | grep putio-download | grep -v grep | wc -l`
if [ $COUNT == 0 ]; then
    putio-download --config ~/config.ini
else
	echo "already running..."
fi
```

*If you do use a script like this, make sure to update the crontab to point to it*
