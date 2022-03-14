import logging

import cv2
import numpy
import pytesseract
import requests

from config import DEAN_URL, STUDENT_ID, PASSWORD

DEAN_INDEX_PATH = "service/login.html"
POST_LOGIN_FORM_PATH = "vatuu/UserLoginAction"
POST_USER_LOADING_PATH = "vatuu/UserLoadingAction"
GET_CAPTCHA_IMG_PATH = "vatuu/GetRandomNumberToJPEG"


def break_captcha(img_data: numpy.array):
    captchaImg = cv2.imdecode(img_data, cv2.IMREAD_GRAYSCALE)
    captchaImg = captchaImg[2:, 1:]
    captchaImg = cv2.resize(captchaImg, (500, 200), interpolation=cv2.INTER_LINEAR)
    captchaImg = cv2.threshold(captchaImg, 110, 255, cv2.THRESH_BINARY)[1]
    captchaImg = cv2.morphologyEx(captchaImg, cv2.MORPH_CLOSE, None)
    captchaResult = pytesseract.image_to_string(captchaImg, lang='eng')[:-1]
    return captchaResult


def login(r: requests.session):
    try:
        headers = {
            # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
            # "Accept": "application/json, text/javascript, */*; q=0.01",
            # "Host": DEAN_URL.split(":", 1)[1][2:].split("/",1)[0],
            # "Origin": INSECURE_DEAN_URL if use_insecure else SECURE_DEAN_URL[:-4],

            # referer and charset must be set to send post for this dean system
            "Referer": DEAN_URL + DEAN_INDEX_PATH,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        r.get(url=DEAN_URL + DEAN_INDEX_PATH)

        for i in range(0, 5):
            img_request = r.get(url=DEAN_URL + GET_CAPTCHA_IMG_PATH)
            captchaImg = numpy.asarray(bytearray(img_request.content), dtype="uint8")
            captchaResult = break_captcha(captchaImg)
            if captchaResult == None or len(captchaResult) != 4:
                continue
            postData = {
                "username": STUDENT_ID,
                "password": PASSWORD,
                "ranstring": captchaResult,
                # "url": "",
                # "returnUrl": "",
                # "returnType": "",
                # "area": "",
            }
            headers.update()
            res = r.post(
                url=DEAN_URL + POST_LOGIN_FORM_PATH,
                data=postData,
                headers=headers
            )
            if res.json()["loginStatus"] != "1":
                continue
            r.post(url=DEAN_URL + POST_USER_LOADING_PATH)
            return True
        logging.error("login failed 5 times")
        return False

    except r.exceptions.RequestException as e:
        logging.error(e)
        logging.error("login failed")
        return False
