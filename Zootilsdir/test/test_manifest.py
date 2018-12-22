import pytest
from panoptes_client.panoptes import PanoptesAPIException
from unittest.mock import patch
import unittest
from JamesLab.Zootils.manifest import manifest
import os.path as osp
import os
from optparse import OptionParser as optpar
from glob import glob


def test_manifest():

    imgdir = osp.join(osp.getcwd(), 'img')

    manifest(imgdir)
    mani_path = osp.join('img', 'manifest.csv')
    assert osp.exists(mani_path)
    with open(mani_path, 'r') as manf:
        lines = manf.readlines()
    assert len(lines) == (len(glob(osp.join(imgdir, '*.png'))) + len(glob(osp.join(imgdir, '*.jpg')))) + 1

    manifest(imgdir, ext='png')
    mani_path = osp.join('img', 'manifest.csv')
    assert osp.exists(mani_path)
    with open(mani_path, 'r') as manf:
        lines = manf.readlines()
    assert len(lines) == len(glob(osp.join(imgdir, '*.png'))) + 1

    manifest(imgdir, ext='jpg')
    mani_path = osp.join('img', 'manifest.csv')
    assert osp.exists(mani_path)
    with open(mani_path, 'r') as manf:
        lines = manf.readlines()
    assert len(lines) == len(glob(osp.join(imgdir, '*.jpg'))) + 1

    os.remove(osp.join(imgdir, 'manifest.csv'))
