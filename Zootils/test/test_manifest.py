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

    manifest('img')

    mani_path = osp.join('img', 'manifest.csv')
    assert osp.exists(mani_path)

    with open(mani_path, 'r') as manf:
        lines = manf.readlines()

    assert len(lines) == ( len(glob('img/*.png')) + len(glob('img/*.jpg')) ) + 1

    manifest('img', ext='png')

    mani_path = osp.join('img', 'manifest.csv')
    assert osp.exists(mani_path)

    with open(mani_path, 'r') as manf:
        lines = manf.readlines()

    assert len(lines) == len(glob('img/*.png')) + 1

    manifest('img', ext='jpg')

    mani_path = osp.join('img', 'manifest.csv')
    assert osp.exists(mani_path)

    with open(mani_path, 'r') as manf:
        lines = manf.readlines()

    assert len(lines) == len(glob('img/*.jpg')) + 1
