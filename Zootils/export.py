from getpass import getpass
import sys
import os.path as osp
import os
from datetime import datetime as dt
import csv
import logging
import re
from JamesLab.Zookeeper import utils
try:
    from panoptes_client import Panoptes, Project
    from panoptes_client.panoptes import PanoptesAPIException
except ImportError:
    print("panoptes_client package could not be imported. To install use:")
    print("> pip install panoptes-client")
    print("Or activate your panoptes-client enabled environment")
    exit(False)


log = utils.get_logger()


def export(args, opts):
    '''
    %prog export project_id output_dir

    Does:
        Fetches export from zooniverse for specified project.

    Args:
        - project_id
            -type: str
            -desc: The zooniverse project id
        - output_dir
            -type: str
            -desc: Path to the image directory with images to be uploaded
    Returns:
        None
    '''

    proj_id, output_dir = args

    if not osp.isdir(output_dir):
        log.error("Output directory does not exist")
        return False

    project = utils.connect(proj_id)

    try:
        log.info("Getting export, this may take a lot of time.")
        export = project.get_export(opts.type)
        count = 0
        while (osp.isfile("export_{}.zoo.csv".format(count))):
            count += 1
        with open(
                  osp.join(output_dir,
                           "export_{}.zoo.csv".format(count)
                           ),
                  'w') as zoof:
            zoof.write(export)
    except PanoptesAPIException as e:
        log.error("Error getting export")
        for arg in e.args:
            log.error("> " + arg)
        return False

    return True
