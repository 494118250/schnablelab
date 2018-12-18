from JamesLab.Zookeeper.zookeeper import zootils
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
from datetime import datetime as dt
from collections import deque
from random import random

cred = {'un': 'alejandropages', 'pw': '12Buckl3mYSh03'}

img_dir = osp.abspath('/home/apages/SchnableLab/JamesLab/ImgPros/tests/data/imgs')
img_no_man = osp.abspath('/home/apages/SchnableLab/JamesLab/ImgPros/tests/data/imgs_no_manifest')
real_proj_id = '7802'
real_subjset_id = '67200'
fake_id = '567'

'''
def test_upload():

    args = [cred['un'], str(int(random() * 1000))]

    with mock.patch('builtins.input', side_effect=args):
        assert zootils.upload([img_no_man, '6761'])

    os.remove(osp.join(img_no_man, 'manifest.csv'))
'''

def test_connect():

    zoo = zootils()

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zoo._connect(fake_id, un=cred['un'], pw=cred['pw'])

    with pytest.raises(pan.panoptes.PanoptesAPIException):
        zoo._connect(real_proj_id, un='foo', pw='bar')

    assert zoo._connect(real_proj_id, un=cred['un'], pw=cred['pw'])
    assert hasattr(zoo, 'project')


'''mock.patch('builtins.input', side_effect=args),\
     '''
r'''

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

def test___log_error():

    messages = ("Error Logging Message", "args test 1", "args test 2")

    zookeeper.__log_error(messages[0])
    with pytest.raises(pan.panoptes.PanoptesAPIException):
        e = pan.panoptes.PanoptesAPIException
        e.args = messages[1:3]
        zookeeper.__log_error("TEST MESSAGE (error logging)", e)

    # matches time isoformat with optional '.(microseconds)'
    PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.?\d*?: " +
                         "TEST MESSAGE (error logging)\n> args test 1\n> args test 2\n")

    with open(osp.normpath('../zoo_load.err'), 'r') as file:
        last3 = deque(file, 3)
        assert PATTERN.match("".join(last3))
'''
