import datetime
import re

import pandas as pd
import requests
from pandas import DataFrame

from config import DEAN_URL, ICAL_FILE_NAME

GET_SCHEDULE_WEBPAGE_PATH = "vatuu/CourseAction"
CURRENT_TERM_COURSE_SCHEDULE_PARAMS = {
    "setAction": "userCourseSchedule",
    "selectTableType": "ThisTerm"
}
CURRENT_TERM_FIRST_WEEK_COURSE_SCHEDULE_PARAMS = {
    "setAction": "userCourseScheduleTable",
    "viewType": "studentCourseTableWeek",
    "selectTableType": "ThisTerm",
    "queryType": "student",
    "weekNo": "1"
}

REGEX_TIME = re.compile(r"^([0-9,-]+)周 星期(.) ([0-9,-]+)节$")
REGEX_DETAILS = re.compile(r"^X([0-9]+)\((.+?)\)(\(.+\))?(#.+)?")
WEEK_ZH_DAY_OFFSET = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6}
CLASS_START_TIMES = (
    (8, 0), (8, 50), (9, 50), (10, 40), (11, 30),
    (14, 0), (14, 50), (15, 50), (16, 40), (17, 30),
    (19, 30), (20, 20), (21, 20)
)
CLASS_END_TIMES = (
    (8, 45), (9, 35), (10, 35), (11, 25), (12, 15),
    (14, 45), (15, 35), (16, 35), (17, 25), (18, 15),
    (20, 15), (21, 5), (21, 55)
)

ICAL_VEVENT_START = "BEGIN:VEVENT" + "\r\n" + \
                    "SUMMARY:{title}" + "\r\n" + \
                    "UID:{code}-{start}" + "\r\n" + \
                    "DTSTAMP:{ts}Z" + "\r\n" + \
                    "DTSTART;TZID=Asia/Shanghai:{start}" + "\r\n" + \
                    "DTEND;TZID=Asia/Shanghai:{end}" + "\r\n" + \
                    "LOCATION:{location}" + "\r\n" + \
                    "DESCRIPTION:Lecturer(s):{lecturer}\\nCode:{code}\\nClass Number:{class_num}" + "\r\n"

ICAL_VEVENT_REPEAT = "RRULE:FREQ=WEEKLY;COUNT={count}" + "\r\n"

ICAL_VEVENT_END = "END:VEVENT" + "\r\n"

ICAL_START = "BEGIN:VCALENDAR" + "\r\n" + \
             "VERSION:2.0" + "\r\n" + \
             "PRODID:-//RFYoung/SWJTU Course Schedule Kit//EN" "\r\n" + \
             "BEGIN:VTIMEZONE" "\r\n" + \
             "TZID:Asia/Shanghai" "\r\n" + \
             "BEGIN:STANDARD" "\r\n" + \
             "TZOFFSETFROM:+0800" "\r\n" + \
             "TZOFFSETTO: +0800" "\r\n" + \
             "TZNAME:CST" "\r\n" + \
             "DTSTART:19700101T000000" "\r\n" + \
             "END:STANDARD" "\r\n" + \
             "END:VTIMEZONE" "\r\n"

ICAL_END = "END:VCALENDAR"

TS_FORMAT = "%Y%m%dT%H%M%S"


def write_schedule(r: requests):
    schedule_webpage = r.get(url=DEAN_URL + GET_SCHEDULE_WEBPAGE_PATH, params=CURRENT_TERM_COURSE_SCHEDULE_PARAMS)
    df_list = pd.read_html(schedule_webpage.text)
    df = df_list[1].iloc[:-1, :-3]

    year = get_start_year(df)
    first_day = get_first_day(year, r)

    with open(ICAL_FILE_NAME, "w") as f:
        f.write(ICAL_START)

    for index, row in df.iterrows():
        time_and_detail = row["上课时间地点"].split("  ")
        times = time_and_detail[0::2]
        details_by_time = time_and_detail[1::2]
        c = Course(name=row["课程名称"],
                   lecturers=row["任课教师"],
                   course_code=row["课程代码"],
                   class_num=row["班号"],
                   times=times,
                   details_by_time=details_by_time)
        c.write_ical_event(first_day)

    with open(ICAL_FILE_NAME, "a") as f:
        f.write(ICAL_END)


def get_start_year(main_df: DataFrame):
    term = main_df.iloc[0, 1]
    t_match = re.compile(r"([0-9]{4})-([0-9]{4})第([1,2])学期").match(term)
    year = int(t_match.group(1)) if t_match.group(3) == '1' else int(t_match.group(2))
    return year


def get_first_day(year: int, r: requests):
    schedule_first_week_webpage = r.get(url=DEAN_URL + GET_SCHEDULE_WEBPAGE_PATH,
                                        params=CURRENT_TERM_FIRST_WEEK_COURSE_SCHEDULE_PARAMS)
    df_list = pd.read_html(schedule_first_week_webpage.text)
    match = re.compile(r".*([0-9]{2})月([0-9]{2})").match(df_list[1].iloc[0, 2])
    return datetime.date(year, int(match.group(1)), int(match.group(2)))


class Course:
    def __init__(self, name: str, lecturers: str, course_code: str, class_num: str, times: list, details_by_time: list):
        self.name = name
        self.times = times
        self.course_code = course_code
        self.lecturers = lecturers
        self.class_num = int(float(class_num))
        self.details_by_time = details_by_time

    def write_ical_event(self, first_day):
        with open(ICAL_FILE_NAME, "a") as f:
            for i in range(0, len(self.times)):
                match_time = REGEX_TIME.match(self.times[i])
                # print(self.times[i])
                match_details = REGEX_DETAILS.match(self.details_by_time[i])
                week_nums = match_time.group(1)
                day_of_weak = WEEK_ZH_DAY_OFFSET[match_time.group(2)]
                course_event_index_of_day = match_time.group(3)
                room = match_details.group(1)
                campus = match_details.group(2)
                lecturer_pts = match_details.group(3)
                lecturer = lecturer_pts[1:-1] if lecturer_pts is not None else self.lecturers
                if match_details.group(4) is None:
                    course_event_type = group_num = ""
                else:
                    course_event_type_group_num = match_details.group(4).split('#')
                    course_event_type = course_event_type_group_num[1][:3] + "_"
                    group_num = course_event_type_group_num[2] + "_" if len(course_event_type_group_num) == 3 else ""

                for weeks_nums_near in week_nums.split(','):
                    weeks_nums_near_list = weeks_nums_near.split('-')
                    start_week_num = int(weeks_nums_near_list[0])
                    start_days_delta = day_of_weak + 7 * (start_week_num - 1)
                    start_day = first_day + datetime.timedelta(days=start_days_delta)
                    for course_event_index_of_day_near in course_event_index_of_day.split(','):
                        course_event_index_of_day_near_list = course_event_index_of_day_near.split('-')
                        start_time = CLASS_START_TIMES[int(course_event_index_of_day_near_list[0]) - 1]
                        start_datetime = datetime.datetime.combine(
                            start_day,
                            datetime.time(start_time[0], start_time[1])
                        )
                        end_event_index_of_day = int(course_event_index_of_day_near_list[0]) \
                            if len(course_event_index_of_day_near_list) == 1 \
                            else int(course_event_index_of_day_near_list[1])
                        end_time = CLASS_END_TIMES[int(end_event_index_of_day) - 1]
                        end_datetime = datetime.datetime.combine(
                            start_day,
                            datetime.time(end_time[0], end_time[1])
                        )
                        ts = datetime.datetime.utcnow()
                        title = course_event_type + group_num + self.name
                        f.write(ICAL_VEVENT_START.format(title=title,
                                                         code=self.course_code,
                                                         ts=ts.strftime(TS_FORMAT),
                                                         start=start_datetime.strftime(TS_FORMAT),
                                                         end=end_datetime.strftime(TS_FORMAT),
                                                         location="X" + room + "_" + campus,
                                                         lecturer=lecturer,
                                                         class_num=self.class_num
                                                         ))
                        if len(weeks_nums_near_list) == 2:
                            count = int(weeks_nums_near_list[1]) - start_week_num + 1
                            f.write(ICAL_VEVENT_REPEAT.format(count=count))
                        f.write(ICAL_VEVENT_END)
