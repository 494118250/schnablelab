import pytest
from panoptes_client.panoptes import PanoptesAPIException
import unittest as ut
from unittest.mock import patch
import unittest
from JamesLab.Zootils import upload
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

    # valid_args
    valid = {'projid':8103, 'imgdir':osp.normpath('img')}
    default_opts = opts()

    # TEST assert manifest generated
    with patch('builtins.input', side_effect=['cmiao@huskers.unl.edu']):
        upload(valid['imgdir'], valid['projid'], default_opts)

    # TEST 2
