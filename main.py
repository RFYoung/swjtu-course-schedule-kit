import requests

from login import login
from schedule import write_schedule
from sftp_upload import upload_ical


def main():
    r = requests.session()
    if login(r) is False:
        exit(1)
    write_schedule(r)
    upload_ical()


if __name__ == "__main__":
    main()
