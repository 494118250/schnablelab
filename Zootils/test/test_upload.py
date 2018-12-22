import pytest
from panoptes_client.panoptes import PanoptesAPIException
from unittest.mock import patch
import unittest
from JamesLab.Zootils.upload import upload
import os.path as osp
import os
from optparse import OptionParser as optpar


class opts:

    def __init__(self, subject=None, quiet=False, workflow=None, convert=False):
        self.subject = subject
        self.quiet = quiet
        self.workflow = workflow
        self.convert = convert


def test_upload():

    # TEST 1
    projid = 8103
    imgdir = 'img'
    opts = opts()

    osp.remove(osp.join('img', 'manifest.csv'))
    upload(imgdir, projid, opts)
    assert osp.exists(osp.join('img', 'manifest.csv'))

    # TEST 2
    
