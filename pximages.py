#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# this script was made in reference to http://kennn.hatenablog.com/entry/2016/10/18/234950
# download the all images from the give pixiv userid.

import os
import sys
import time
import json
import getpass
import argparse
import pixivpy3
import tqdm


class PXImages():
    def __init__(self):
        self.json_path = os.path.abspath(os.path.expanduser("~/.pximages"))
        self.api = pixivpy3.PixivAPI()
        self.aapi = pixivpy3.AppPixivAPI()
        with open(self.json_path, 'r') as f:
            t = json.load(f)
        self.client_info = t
        self.user_id = 0
        self.user_name = ""
        self.out_dir = ""
        self.dst_dir = ""
        self.total_works = 0
        self.URLs = []
        self.max_page_num = 1

    def check_json(self):
        if not os.path.exists(self.json_path):
            print("Pixiv conf file is not at %s. Make conf file." % self.json_path)
            pxid = input('Type pixiv id: ')
            pxpasswd = getpass.getpass(prompt="Type pixiv password: ")
            d = {"pixiv_id": pxid, "pixiv_password": pxpasswd}
            with open(self.json_path, "w") as f:
                json.dump(d, f)

    def login(self):
        pixiv_id = self.client_info['pixiv_id']
        pixiv_password = self.client_info['pixiv_password']
        self.api.login(pixiv_id, pixiv_password)

    def pre_conf(self, user_id, out_dir):
        self.user_id = user_id
        self.out_dir = os.path.abspath(os.path.expanduser(out_dir))

    def make_dst_dir(self):
        self.dst_dir = self.out_dir + \
            "/pixiv_images/%s (%s)/" % (self.user_name, self.user_id)
        if not os.path.exists(self.dst_dir):
            os.makedirs(self.dst_dir)

    def get_json(self, user_id, page_number):
        json_result = self.api.users_works(
            int(user_id), page=int(page_number), per_page=30)
        if int(page_number) == 1:
            self.total_works = int(json_result.pagination.total)
            r = self.total_works % 30
            if r == 0:
                self.max_page_num = (self.total_works - r) / 30
            if r != 0:
                self.max_page_num = (self.total_works - r) / 30 + 1
            self.user_name = json_result.response[0].user.name
        return json_result

    def get_image_urls(self):
        c = 1
        while True:
            json_result = self.get_json(self.user_id, c)  # get max_page_num
            if c == 1:
                self.make_dst_dir()
            illusts_json = json_result.response
            if illusts_json == []:
                print("Given user_id '%s' is incorrect." % self.user_id)
                sys.exit()
            self.append_extracted_image_urls(illusts_json)
            if self.max_page_num == c:
                break
            c += 1

    def append_extracted_image_urls(self, illusts_json):
        for data in illusts_json:
            pc = int(data.page_count)
            sys.stdout.write("\r")
            if pc == 1:
                url = data.image_urls['large']
                self.URLs.append(url)
                sys.stdout.write(
                    "\rRetrieving images from Pixiv API: found {0} images.".format(len(self.URLs)))
            if pc > 1:
                base_url = data.image_urls['large']
                part1, part2 = os.path.split(base_url)
                name, ext = part2.split('.')
                temp_urls = ["%s/%s%s.%s" % (part1, name[:-1], n, ext)
                             for n in range(0, pc)]
                self.URLs = self.URLs + temp_urls
                sys.stdout.write(
                    "\rRetrieving images from Pixiv API: found {0} images.".format(len(self.URLs)))
            sys.stdout.flush()
            time.sleep(0.1)

    def download_images(self):
        pbar = tqdm.tqdm(self.URLs, unit=' imgs')
        for url in pbar:
            file_name = url.split('/')[-1]
            pbar.set_description("Downloading %s from %s (id: %s)" %
                                 (file_name, self.user_name, self.user_id))
            self.aapi.download(url, self.dst_dir)
            pbar.update()

    def main(self):
        parser = argparse.ArgumentParser(
            description="Download all images from given pixiv user id.")
        parser.add_argument("-u", "--user", dest="user_id", metavar="user_id",
                            required=True, type=int, nargs="*", help="Pixiv UserID(s).")
        parser.add_argument("-o", "--output", dest="out_dir", metavar="output_dir", type=str, nargs="?", default=".",
                            help="Output dir (default: current dir). All images will be downloaded under [output_dir]/pixiv_images/user_name")
        args = parser.parse_args()
        user_ids = args.user_id
        out_dir = args.out_dir
        self.check_json()
        self.login()
        for user_id in user_ids:
            self.pre_conf(user_id, out_dir)
            sys.stdout.write("\rRetrieving images from Pixiv API: ")
            self.get_image_urls()
            sys.stdout.write("\n")
            self.download_images()


def main():
    Pixiv = PXImages()
    Pixiv.main()


if __name__ == '__main__':
    main()
