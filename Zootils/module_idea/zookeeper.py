from getpass import getpass
import sys
import os.path as osp
import os
from datetime import datetime as dt
import csv
import logging
import re
try:
    from panoptes_client import Panoptes, Project
    from panoptes_client.panoptes import PanoptesAPIException
except ImportError:
    print("panoptes_client package could not be imported. To install use:")
    print("> pip install panoptes-client")
    print("Or activate your panoptes-client enabled environment")
    exit(False)


class zootils():

    def __init__(self):
        '''
        Set logging objects
        '''
        self._log = logging.getLogger('zootils')

        self._log.setLevel(logging.DEBUG)
        # For outputting logs to files
        self._log.addHandler(logging.FileHandler('zoo_load.err'))
        # for output to stdout and stderr
        self._log.addHandler(logging.StreamHandler())

    def _connect(self, projid, **kwargs):
        ''' Override of panoptes connect method '''

        if 'un' in kwargs and 'pw' in kwargs:
            un = kwargs['un']
            pw = kwargs['pw']
        else:
            un = input("Enter zooniverse username: ")
            pw = getpass()
        try:
            Panoptes.connect(username=un, password=pw)
            self._project = Project.find(id=projid)
        except PanoptesAPIException as e:
            self._log.error("Could not connect to zooniverse project")
            for arg in e.args:
                self._log.error("> " + arg)
            raise

        return True

    def __get_yn(message):
        while True:
            val = input(message + " [y/n]")
            if val.lower() in ['y', 'n']:
                return True if val.lower() == 'y' else False
            else:
                print("Invalid input")

    def generate_manifest(self, imgdir, ext=None):

        if not osp.isdir(imgdir):
            self.log.error("Image directory '{}' does not exist"
                           .format(imgdir))
        self.log.info("Manifest being generated with fields: [ id, filename ]")

        mfile = open(osp.join(imgdir, 'manifest.csv'), 'r')
        writer = csv.writer(mfile)
        writer.writerow(["id", "filename"])

        idtag = dt.now().strftime("%m%d%y-%H%M%S")

        if not ext:
            PATTERN = re.compile(r".*\.(jpg|png|tiff)")
        elif ext == 'jpg':
            PATTERN = re.compile(r".*\.jpg")
        elif ext == 'png':
            PATTERN = re.compile(r".*\.png")
        elif ext == 'tiff':
            PATTERN = re.compile(r".*\.tiff")

        img_c = 0
        for id, filename in enumerate(os.listdir(imgdir)):
            if PATTERN.match(filename):
                writer.writerow(["{}-{:04d}".format(idtag, id),
                                 osp.join(imgdir, filename)])
                img_c += 1
            if img_c == 9999:
                self.log.warning("Zooniverse's default limit of subjects per"
                                 + " user is 9999. You may not be able to load"
                                 + " this entire subject set.")
                if not self.__get_yn("Continue?"):
                    break
                img_c += 1

        self.log.info("DONE: {} subjects written to manifest"
                      .format(img_c))

        mfile.close()
        return True
