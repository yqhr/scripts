#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
import json
from pytz import timezone
import getpass
import argparse
import requests
from dateutil.parser import parse as dtparse


class Toggl():
    def __init__(self):
        self.session = requests.session()
        self.rootURL = "https://www.toggl.com/api/v8"
        self.token_path = "~/.toggl_token"
        self.api_token = ""
        self.current_task = {}
        self.auth_tuple = ()
        self.json_headers = {"Content-Type": "application/json"}
        self.default_wid = 0
        self.task_running = False

    def GetUserInfo(self):
        if not os.path.exists(self.token_path):
            print (
                "There does not seem a token file. This program will get it from now.")
            mail = input("Type your email in Toggl: ")
            password = getpass.getpass(prompt="Type the password: ")
            print("=> Retrieving your api token from Toggl's API.")
            URL = "%s/me" % self.rootURL
            s = self.session.get(URL, auth=(mail, password))
            gotJSON = json.loads(s.text)
            APIKey = gotJSON['data']['api_token']
            default_wid = gotJSON['data']['default_wid']
            self.WriteUserInfo(APIKey, default_wid)
            self.api_token = APIKey
            self.default_wid = default_wid

    def WriteUserInfo(self, token, wid):
        if not os.path.exists(self.token_path):
            with open(self.token_path, "w") as f:
                json.dump({'api_token': token, "default_wid": wid}, f)

    def ReadFromLocal(self):
        if os.path.exists(self.token_path):
            with open(self.token_path, "r") as f:
                data = json.load(f)
            self.api_token = data['api_token']
            self.default_wid = data['default_wid']

    def SetToken(self):
        self.GetUserInfo()
        if not any((self.api_token, self.default_wid)):
            self.ReadFromLocal()
        self.auth_tuple = (self.api_token, "api_token")

    def RetrieveCurrentTask(self):
        URL = "%s/time_entries/current" % (self.rootURL)
        s = self.session.get(URL, auth=self.auth_tuple)
        self.current_task = json.loads(s.text)

    def CheckTaskStarted(self):
        if isinstance(self.current_task, dict):
            entry = self.current_task['data']
            if entry is not None:
                flag = 'stop' not in entry
                self.task_running = flag

    def StopCurrentTask(self):
        if self.task_running:
            entry = self.current_task['data']
            entry_id = entry['id']
            entry_name = ""
            if 'description' in entry:
                entry_name = entry['description']
            URL = "%s/time_entries/%s/stop" % (self.rootURL, entry_id)
            s = self.session.put(
                URL, headers=self.json_headers, auth=self.auth_tuple
            )
            resultJSON = json.loads(s.text)
            finish_time = self.UTC2JST(dtparse(resultJSON['data']['stop']))
            print("=> Stop the current task: '%s' (at %s)." %
                  (entry_name, finish_time))
        else:
            print("Failed to stop a task. No task seems to be running.")

    def StartNewTask(self, description):
        data = {
            "time_entry": {
                "description": description,
                "wid": int(self.default_wid),
                "tags": ["pytoggl"],
                "created_with": "pytoggl"
            }
        }
        URL = "%s/time_entries/start" % self.rootURL
        s = self.session.post(
            URL, data=json.dumps(data),
            headers=self.json_headers, auth=self.auth_tuple
        )
        resultJSON = json.loads(s.text)
        start_time = self.UTC2JST(dtparse(resultJSON['data']['start']))
        print("=> Start a new task: '%s' (at %s)." % (description, start_time))

    def ShowCurrentTask(self):
        if self.task_running:
            data = self.current_task['data']
            description = data['description']
            jst_time = self.UTC2JST(dtparse(data['start']))
            print("\r=> Current task: '%s' (started at %s)." %
                  (description, jst_time))
        else:
            print("No task seems to be running.")

    def UTC2JST(self, utc_time):
        return utc_time.astimezone(timezone('Asia/Tokyo'))

    def main(self):
        mangle_args = ('show', 'start', 'stop', 'help')
        arguments=['--%s' % arg if arg in mangle_args else arg for arg in sys.argv[1:]]
        parser = argparse.ArgumentParser(
            description="Toggl control by python.", prog="pytoggl",
            usage='%(prog)s (start [description] | stop | show | help)'
        )
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--start", metavar="description",
                           dest="start", type=str, nargs="?",
                           default=argparse.SUPPRESS,
                           help="Start a task with the description.")
        group.add_argument("--stop", action="store_true",
                           help="Stop a running task.")
        group.add_argument("--show", action="store_true",
                           help="Show a current task.")
        args = vars(parser.parse_args(arguments))
        self.SetToken()
        if 'start' in args:
            if args['start'] is None:
                description = ""
            else:
                description = args['start']
            self.StartNewTask(description)
        self.RetrieveCurrentTask()
        self.CheckTaskStarted()
        if args['show']:
            self.ShowCurrentTask()
        if args['stop']:
            self.StopCurrentTask()
        self.session.close()


def main():
    toggl = Toggl()
    toggl.main()


if __name__ == '__main__':
    main()
