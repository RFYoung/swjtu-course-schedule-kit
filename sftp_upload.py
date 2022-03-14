import logging
import paramiko

from paramiko.ssh_exception import SSHException

from config import UPLOAD_HOST, UPLOAD_USER, ICAL_FILE_NAME, UPLOAD_DIRECTORY, PRIVATE_KEY_FILE_PATH


def upload_ical():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key = paramiko.RSAKey.from_private_key_file(PRIVATE_KEY_FILE_PATH)
        ssh.connect(UPLOAD_HOST, username=UPLOAD_USER, pkey=key)
        sftp_client = ssh.open_sftp()
        sftp_client.put(ICAL_FILE_NAME, UPLOAD_DIRECTORY + ICAL_FILE_NAME)
        ssh.close()
    except SSHException as e:
        logging.error("upload failed")
        logging.error(str(e))
