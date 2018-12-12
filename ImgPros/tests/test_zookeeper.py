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
import panoptes_client as pan

cred = {'un': 'alejandropages', 'pw': '12Buckl3mYSh03'}

img_dir = osp.join(osp.dirname(__file__), 'data', 'imgs')
img_no_man = osp.join(osp.dirname(__file__), 'data', 'imgs_no_manifest')
real_proj_id = '7802'
real_subjset_id = '67200'
fake_id = '567'


def test___check_dir():
    with pytest.raises(IOError) as e:
        zookeeper.__check_dir("doesntexist")


def test___generate_manifest():

    with pytest.raises(FileNotFoundError):
        zookeeper.__generate_manifest("NonexistentFile")

    mfile = zookeeper.__generate_manifest(img_dir)
    assert osp.exists(osp.join(img_dir, 'manifest.csv'))

    PATTERN = re.compile(r".*\.(jpg|png|tiff)")
    assert sum(1 for i in mfile.readlines()) - 1 == len([i for i in os.listdir(img_dir) if PATTERN.match(i)])


def test_manifest(capsys):

    with pytest.raises(SystemExit):
        err = zookeeper.manifest(["NonexistentFile"])



def test___connect_zoo():

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zookeeper.__connect_zoo(fake_id, un=cred['un'], pw=cred['pw'])

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zookeeper.__connect_zoo(real_proj_id, un='foo', pw='bar')

    assert type(zookeeper.__connect_zoo(real_proj_id, un=cred['un'], pw=cred['pw'])) == pan.project.Project




def test_upload():

    with pytest.raises(SystemExit) as e:
        zookeeper.upload(['DNE', real_proj_id])
        assert e.value.code == -1

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zookeeper.upload([img_dir, real_proj_id],
                         'fubar', 'chicken')

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zookeeper.upload([img_dir, fake_id])

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zookeeper.upload([img_dir, real_proj_id],
                         cred['un'], cred['pw'],
                         dispname='test_subject')

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zookeeper.upload([img_dir, real_proj_id],
                         cred['un'], cred['pw'],
                         subjsetid=fake_id)

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zookeeper.upload([img_no_man, real_proj_id],
                         cred['un'], cred['pw'],
                         subjsetid=real_subjset_id)


def test_export():

    zookeeper.export([fake_id, osp.dirname(__file__)])
