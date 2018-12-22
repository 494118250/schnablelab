from getpass import getpass
import sys
import os.path as osp
import os
from datetime import datetime as dt
import csv
import logging
import re
from JamesLab.Zootils import utils
try:
    from panoptes_client import Panoptes, Project
    from panoptes_client.panoptes import PanoptesAPIException
except ImportError:
    print("panoptes_client package could not be imported. To install use:")
    print("> pip install panoptes-client")
    print("Or activate your panoptes-client enabled environment")
    exit(False)


log = logging.getLogger(__name__)


def export(projid, outfile, opts):
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

    project = utils.connect(projid)

    try:
        log.info("Getting export, this may take a lot of time.")
        export = project.get_export(opts.type)
        with open(outfile, 'w') as zoof:
            zoof.write(export.text)
    except PanoptesAPIException as e:
        log.error("Error getting export")
        for arg in e.args:
            log.error("> " + arg)
        return False

    return True
