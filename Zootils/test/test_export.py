import pytest
from panoptes_client.panoptes import PanoptesAPIException
from unittest.mock import patch
import unittest
from JamesLab.Zootils.export import export
import os.path as osp
import os
from optparse import OptionParser as optpar


def test_export():

    user_creds = ['alejandropages', '12Buckl3mYSh03']

    class opts:
        def __init__(self):
            self.type = 'classifications'

    opts = opts()

    if osp.exists('export.csv'):
        os.remove('export.csv')

    @patch('getpass.getpass')
    @patch('builtins.input')
    export(7802, 'export.csv', opts)

    assert osp.exists('export.csv')
    osp.remove('export.csv')
