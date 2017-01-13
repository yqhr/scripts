#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Check websites' update and sent email if there is update.

import os
import sys
import datetime
import requests
import smtplib
from bs4 import BeautifulSoup
from email.mime.text import MIMEText


class CheckUpdate():
    def __init__(self):
        self.URL = ""
        self.session = requests.Session()

    def GetLM(self):
        header = self.session.head(self.URL)
        result = header.headers
        last_updated_time = datetime.datetime.strptime(
            result['Last-Modified'], "%a, %d %b %Y %H:%M:%S GMT")
        return last_updated_time

    def GetTitle(self):
        get = self.session.get(self.URL)
        soup = BeautifulSoup(get.text.encode(get.encoding), 'lxml')
        title = soup.title.text
        return title

    def check_update(self):
        gLM = self.GetLM()
        root_dir = os.path.abspath(os.path.expanduser("~/check_update"))
        sub_dir, file_name = os.path.split(self.URL.split('//')[1])
        if not file_name:
            file_name = "index.html"
        file_dir = "%s/%s" % (root_dir, sub_dir)
        file_path = "%s/%s.txt" % (file_dir, file_name)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("%s" % gLM)
            print("Given URL is up-to-date.")
            return False
        else:
            with open(file_path, "r") as f:
                rLM = f.read()
            fLM = datetime.datetime.strptime(rLM, "%Y-%m-%d %H:%M:%S")
            LM_latest, flag_update = self.CompareLM(gLM, fLM)
            if flag_update:
                title = self.GetTitle()
                to = " "
                sub = "[CheckUpdate] '%s' (%s) is updated at %s." % (
                    title, self.URL, LM_latest)
                script_name = os.path.basename(__file__)
                body = "%s (%s) is updated at %s." % (
                    title, self.URL, LM_latest) + \
                    "\nAccess %s to confitm updates!\n" % (self.URL) + \
                    "\n===============================================" + \
                    "\nThis email was sent from a python program, " + \
                    "%s, automatically." % script_name
                self.sendGmail(to, sub, body)
                with open(file_path, "w") as f:
                    f.write("%s" % LM_latest)

    def CheckTypeDT(self, LM):
        if isinstance(LM, datetime.datetime):
            return True
        else:
            return False

    def CompareLM(self, LM1, LM2):
        if self.CheckTypeDT(LM1) and self.CheckTypeDT(LM2):
            if LM1 > LM2:
                return (LM1, True)
            if LM1 < LM2:
                return (LM2, True)
            if LM1 == LM2:
                return (LM1, False)

    # quoted from http://qiita.com/HirofumiYashima/items/1b24397c2e915658c984
    def sendGmail(self, to, sub, body):
        username, password = 'XXXX@gmail.com', 'XXXX'
        host, port = 'smtp.gmail.com', 465
        msg = MIMEText(body)
        msg['Subject'] = sub
        msg['From'] = username
        msg['To'] = to

        smtp = smtplib.SMTP_SSL(host, port)
        smtp.ehlo()
        smtp.login(username, password)
        smtp.mail(username)
        smtp.rcpt(to)
        smtp.data(msg.as_string())
        smtp.quit()

    def main(self):
        gURL = sys.argv[1]
        self.URL = gURL
        self.check_update()


if __name__ == '__main__':
    CU = CheckUpdate()
    CU.main()
