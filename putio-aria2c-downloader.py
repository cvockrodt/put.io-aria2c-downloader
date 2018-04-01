import putiopy
import xmlrpclib
import configparser
import binascii
import time
import os
import ssl
import logging

config = configparser.ConfigParser()
config.read('/var/opt/put.io/config.ini')

OAUTH_TOKEN = config['put.io']['oauth_token']
KEEP_FOLDER_STRUCTURE = config['put.io']['keep_folder_structure']
ARIA2C_SECRET_TOKEN = config['aria2c']['secret_token']
ROOT_DOWNLOAD_DIR = config['aria2c']['root_download_dir']
POST_PROCESS_DIR = config['aria2c']['post_proccess_dir']
WATCH_LIST = dict(config.items('watch_folders'))
LOG_FILE = config['default']['log_file']
RPC_URL = config['aria2c']['rpc_url']

logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(message)s', filename=LOG_FILE, level=logging.INFO)

def download_all_in_watchlist(root_watch_dir=0, download_dir=ROOT_DOWNLOAD_DIR):
    logging.info('Searching for files to download from put.io')
    client = putiopy.Client(OAUTH_TOKEN)
    files = client.File.list(parent_id=root_watch_dir)
    for _file in files:
        if _file.name in WATCH_LIST.values():
            if _file.content_type == 'application/x-directory':
                download_all_in_folder(client, _file, _file.name, download_dir=download_dir)
        else:
            logging.info("File " + _file.name + " not in watchlist")
    client.close()

def cleanup_empty_folders(client, _file):
    files = client.File.list(_file.id)
    if not files:
        if _file.name not in WATCH_LIST.values():
            _file.delete(True)
            logging.info("Deleted " + _file.name + " from put.io")

def download_all_in_folder(client, folder, path="", download_dir=ROOT_DOWNLOAD_DIR):
    files = client.File.list(folder.id)
    for _file in files:
        if _file.content_type == 'application/x-directory':
            folderpath = path + "/" + _file.name
            try:
                logging.info("Making directory " + POST_PROCESS_DIR + folderpath)
                os.mkdir(POST_PROCESS_DIR + folderpath)
            except:
                logging.info("Folder " + folderpath + " already exists")
            download_all_in_folder(client, _file, folderpath, download_dir=download_dir)
            logging.info("Files from " + folderpath + " sent to aria")
            cleanup_empty_folders(client, _file)
        else: 
            download_link = "https://api.put.io/v2/files/" + str(_file.id) + "/download?oauth_token=" + OAUTH_TOKEN
            completed = add_uri(download_link, directory=download_dir + "/" + path)
            if completed:
                logging.info("File " + _file.name + " downloaded successfully by aria")
                _file.delete(True)
                download_path = download_dir + "/" + path + "/" + _file.name
                destination_path = POST_PROCESS_DIR + "/" + path + "/" + _file.name
                os.rename(download_path,destination_path)
            else:
                logging.info("File " + _file.name + " didn't download successfully with aria")
    if not files:
        logging.info("No files to download in " + path)
    
def add_uri(uri, directory=ROOT_DOWNLOAD_DIR):
    token = 'token:'+ ARIA2C_SECRET_TOKEN
    if KEEP_FOLDER_STRUCTURE != 'true':
        directory = ROOT_DOWNLOAD_DIR    
    proxy = xmlrpclib.ServerProxy(RPC_URL)
    opts = {
        "dir": directory, 
        'file-allocation':'falloc',
        'always-resume': 'true',
        'max-connection-per-server': '4',
        'check-integrity': 'true'
    }
    gid = proxy.aria2.addUri(token, [uri], opts)
    loop = True
    while loop:
        time.sleep(2)
        status = proxy.aria2.tellStatus(token, gid, ["gid","status"])
        if status['status'] == 'complete':
            loop = False
            return True
        if status['status'] == 'error':
            loop = False
        if status['status'] == 'removed':
            loop = False
    return False


def crc(filename):
    buf = open(filename,'rb').read()
    buf = (binascii.crc32(buf) & 0xFFFFFFFF)
    return "%08X" % buf

download_all_in_watchlist()
