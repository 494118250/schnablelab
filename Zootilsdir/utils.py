from getpass import getpass
import sys
import os.path as osp
import os
from datetime import datetime as dt
import csv
import logging
import re
from subprocess import run, CalledProcessError
from pprint import pprint
try:
    from panoptes_client import Panoptes, Project
    from panoptes_client.panoptes import PanoptesAPIException
except ImportError:
    print("Error: 'panoptes_client' package could not be imported.")
    print(" To install use: 'pip install panoptes-client'")
    print(" Or activate your panoptes-client enabled environment")
    exit(False)

log = logging.getLogger(__name__)
#log.setLevel(logging.DEBUG)
#log.addHandler(logging.FileHandler(__name__ + '.log'))
#log.addHandler(logging.StreamHandler())


def convert(imgdir, ext=None):
    ''' Image compression and conversion to jpg '''

    cmd = ["mogrify", "-strip", "-quality", "85%", "-format", "jpg"]
    try:
        if ext:
            cmd = cmd.append("*." + ext)
        else:
            cmd.append([osp.join(imgdir, "*.jpg"),
                        osp.join(imgdir, "*.png"),
                        osp.join(imgdir, "*.tiff")])
        proc_ret = run(cmd, capture_output=True)
    except CalledProcessError as e:
        log.error("Failed to compress images")
        pprint(e)

    pprint(proc_ret)
    return True


def connect(projid, **kwargs):
    ''' Override of panoptes connect method '''

    if 'un' in kwargs and 'pw' in kwargs:
        un = kwargs['un']
        pw = kwargs['pw']
    else:
        un = input("Enter zooniverse username: ")
        pw = getpass()
    try:
        Panoptes.connect(username=un, password=pw)
        project = Project.find(id=projid)
    except PanoptesAPIException as e:
        log.error("Could not connect to zooniverse project")
        for arg in e.args:
            log.error("> " + arg)
        raise

    return project


def get_yn(message):
    while True:
        val = input(message + " [y/n]")
        if val.lower() in ['y', 'n']:
            return True if val.lower() == 'y' else False
        else:
            print("Invalid input")
