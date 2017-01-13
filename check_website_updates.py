#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Check websites' update and sent email if there is update.

import os
import sys
import datetime
import requests
import smtplib
import json
import getpass
from bs4 import BeautifulSoup
from email.mime.text import MIMEText


class CheckUpdate():
    def __init__(self):
        self.URL = ""
        self.conf_json = os.path.abspath(
            os.path.expanduser("~/check_update/gmail.json"))
        self.session = requests.Session()
        self.gmail_address = ""
        self.gmail_password = ""

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

    def make_gmail_conf(self):
        if not os.path.exists(self.conf_json):
            print("Gmail conf file is not at %s. Make conf file." %
                  self.conf_json)
            address = input('Type your gmail address: ')
            passwd = getpass.getpass(prompt="Type gmail password: ")
            with open(self.conf_json, "w") as f:
                json.dump({"gmail_address": address,
                           "gmail_password": passwd}, f)
            self.gmail_address = address
            self.gmail_address = passwd

    def check_gmail_conf(self):
        if os.path.exists(self.conf_json):
            with open(self.conf_json, 'r') as f:
                gmail_conf = json.load(f)
            self.gmail_address = gmail_conf['gmail_address']
            self.gmail_password = gmail_conf['gmail_password']
        else:
            self.make_gmail_conf()

    # quoted from http://qiita.com/HirofumiYashima/items/1b24397c2e915658c984
    def sendGmail(self, to, sub, body):
        self.check_gmail_conf()
        host, port = 'smtp.gmail.com', 465
        msg = MIMEText(body)
        msg['Subject'] = sub
        msg['From'] = self.gmail_address
        msg['To'] = to

        smtp = smtplib.SMTP_SSL(host, port)
        smtp.ehlo()
        smtp.login(self.gmail_address, self.gmail_password)
        smtp.mail(self.gmail_address)
        smtp.rcpt(to)
        smtp.data(msg.as_string())
        smtp.quit()

    def main(self):
        gURL = sys.argv[1]
        self.URL = gURL
        self.check_update()
        self.session.close()


if __name__ == '__main__':
    CU = CheckUpdate()
    CU.main()
