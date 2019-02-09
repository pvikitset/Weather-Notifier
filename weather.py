# -*- coding: utf-8 -*-1
import csv
import datetime
import schedule
import time
import json
import sys
import traceback
import urllib.request
from pathlib import Path
import smtplib
import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def get_url(day_location):
    day = '{:{dfmt}}'.format(day_location[0], dfmt='%Y-%m-%d')
    time = '{:{tfmt}}'.format(day_location[0], tfmt='%H:%M:%S')
    location = str(day_location[1][1]) + ',' + str(day_location[1][2])

    return """https://api.darksky.net/forecast/{ACCESS_TOKEN}/{location},{date}T{time}?units=si""".format(
        location=location, date=day, ACCESS_TOKEN=settings.DARKSKY_ACCESS_TOKEN, time=time)


def str_time(unix_time):
    if unix_time is None:
        return None
    else:
        return datetime.datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')

required_fields = [
    "time", "timezone", "temperature", "apparentTemperature", "latitude", "longitude", "summary", "sunriseTime", "sunsetTime",
    "temperatureMin", "temperatureMinTime", "temperatureMax", "temperatureMaxTime", "windGust", "windSpeed"
]


def get_today_and_location(location):
    now = datetime.datetime.today()
    date_and_location_set = set()
    date_and_location_set.add((now, location))
    return date_and_location_set


def get_weather_data(dates_and_locations):
    weather_data = []
    for day_location in dates_and_locations:
        url = get_url(day_location)
        print('Getting data from {}'.format(url))
        try:
            raw_data = json.loads(urllib.request.urlopen(url).read())
            one_day_data = {key: value for key, value in raw_data["currently"].items(
            ) if key in required_fields}
            for required_field in required_fields:
                if required_field not in one_day_data:
                    one_day_data[required_field] = None

            one_day_data['timezone'] = raw_data["timezone"]
            one_day_data['city'] = day_location[1][0]
            one_day_data['latitude'] = day_location[1][1]
            one_day_data['longitude'] = day_location[1][2]
            one_day_data['time'] = str_time(one_day_data['time'])
            one_day_data['sunriseTime'] = str_time(
                raw_data['daily']['data'][0]['sunriseTime'])
            one_day_data['sunsetTime'] = str_time(
                raw_data['daily']['data'][0]['sunsetTime'])
            one_day_data['temperatureMinTime'] = str_time(
                raw_data['daily']['data'][0]['temperatureMinTime'])
            one_day_data['temperatureMaxTime'] = str_time(
                raw_data['daily']['data'][0]['temperatureMaxTime'])

            weather_data.append(one_day_data)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print("Missing data in " + str(day_location))
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, file=sys.stdout)

    return weather_data


def get_report(weather_data):
    data = weather_data[0]
    report = """The weather in <b>{city}</b> at <b>{time}</b><br>
                Today <b>{summary}, with {temperature}</b>.<br>
                The feel like is <b>{apparentTemperature}</b>.<br>
                Wind gust is <b>{windGust}, and speed is <b>{windSpeed}</b><br>
            """.format(city=data['city'],
                       time=data['time'],
                       summary=data['summary'],
                       temperature=data['temperature'],
                       apparentTemperature=data['apparentTemperature'],
                       windGust=data['windGust'],
                       windSpeed=data['windSpeed'])
    return report


def get_html(weather_data):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = settings.SUBJECT
    msg['From'] = settings.BOT_EMAIL
    msg['To'] = settings.TARGET_EMAIL

    html = """\
        <html>
        <head></head>
        <body>
            <p>
            {body}
            </p>
        </body>
        </html>
        """.format(body=get_report(weather_data))

    text = MIMEText(html, 'html')
    msg.attach(text)
    return msg


def sendEmail(sender_email, sender_password, email_destination, html):

    try:
        smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
        smtpObj.ehlo()
        smtpObj.starttls()
        print("Successfully connected to gmail.")

        smtpObj.login(sender_email, sender_password)
        print("Logged In Successfully")

        print("Sending email...")

        smtpObj.sendmail(sender_email, email_destination, html.as_string())
        print("Email sent at {time_stamp}".format(
            time_stamp=datetime.datetime.today().strftime('%H:%M:%S')))

        smtpObj.quit()
    except:
        print("Fail to send email")


def process():
    print("Start process: {}".format(datetime.datetime.now()))
    date_time_and_location = get_today_and_location(settings.LOCATIONS)
    weather_data = get_weather_data(date_time_and_location)
    html = get_html(weather_data)

    sendEmail(settings.BOT_EMAIL, password,
              settings.TARGET_EMAIL, html)

    global is_sent
    is_sent = True


password = input('enter password: -> ')
is_sent = True

if __name__ == '__main__':
    #schedule.every().day.at(settings.TIME_TO_SEND).do(process)
    #schedule.every(1).minute.do(process)
    #schedule.every(10).minutes.do(job)
    #schedule.every().hour.do(job)
    #schedule.every().day.at("10:30").do(job)
    #schedule.every().monday.do(job)f
    #schedule.every().wednesday.at("13:15").do(job)
    #schedule.every().minute.at(":17").do(job)ss
    #schedule.every(1).minute.do(process)
    schedule.every().day.at(settings.TIME_TO_SEND).do(process)
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
            if is_sent:
                print('\nNext process is: ' + datetime.datetime.strftime(schedule.next_run(),'%I:%M:%S%p'))
                is_sent = False
    except KeyboardInterrupt:
        print('interrupted!')
