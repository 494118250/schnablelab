import JamesLab.ImgPros.zookeeper as zookeeper
import os.path as osp
import csv
import os
import re
import pytest
import panoptes_client as pan
import mock
import builtins
import sys
from contextlib import contextmanager
from io import StringIO




def test___generate_manifest():
    img_dir = osp.join(osp.dirname(__file__), 'data', 'imgs')
    mfile = zookeeper.__generate_manifest(img_dir)
    assert osp.exists(osp.join(img_dir, 'manifest.csv'))

    PATTERN = re.compile(".*\.(jpg|png)")
    mfile.seek(0)
    assert sum(1 for i in mfile.readlines()) - 1 == len([i for i in os.listdir(img_dir) if PATTERN.match(i)])


def test_upload():

    img_dir = osp.join(osp.dirname(__file__), 'data', 'imgs')
    proj_id = '7802'

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zookeeper.upload([img_dir, proj_id], 'fubar', 'chicken')

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zookeeper.upload([img_dir, proj_id], 'alejandropages', '12Buckl3mYSh03', dispname='test_subject')
