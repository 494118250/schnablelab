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
    assert sum(1 for i in mfile.readlines()) - 1 == len([i for i in os.listdir(img_dir) if PATTERN.match(i)])


def test_upload():

    cred = {'un': 'alejandropages', 'pw': '12Buckl3mYSh03'}

    img_dir = osp.join(osp.dirname(__file__), 'data', 'imgs')
    img_no_man = osp.join(osp.dirname(__file__), 'data', 'imgs_no_manifest')
    proj_id = '7802'

    with pytest.raises(SystemExit) as e:
        zookeeper.upload(['DNE', proj_id])

    assert e.type == SystemExit
    print("VALUE FROM SYSTEM EXIT: {}".format(e.value.code))
    quit()
    assert e.value.code == -1


    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zookeeper.upload([img_dir, proj_id],
                         'fubar', 'chicken')

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zookeeper.upload([img_dir, proj_id],
                         cred.un, cred.pw,
                         dispname='test_subject')

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zookeeper.upload([img_dir, proj_id],
                         cred.un, cred.pw,
                         subjsetid=567)

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zookeeper.upload([img_no_man, proj_id],
                         cred.un, cred.pw,
                         subjsetid=67200)
