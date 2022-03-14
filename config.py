# change configs below before running
USE_INSECURE_DEAN = False
STUDENT_ID = "201X1XX2XX"
PASSWORD = "dean_pass"
UPLOAD_HOST = "example.com"
UPLOAD_USER = "remote_user"
PRIVATE_KEY_FILE_PATH = "/home/local_user/.ssh/id_rsa"
UPLOAD_DIRECTORY = "/path/of/hosting"
ICAL_FILE_NAME = "swjtu_schedule.ics"

# static variables, do not change unless there is some bug
SECURE_DEAN_URL = "https://jiaowu.swjtu.edu.cn/TMS/"
INSECURE_DEAN_URL = "http://jwc.swjtu.edu.cn/"
DEAN_URL = INSECURE_DEAN_URL if USE_INSECURE_DEAN else SECURE_DEAN_URL
