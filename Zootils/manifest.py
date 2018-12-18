from JamesLab.Zookeeper import utils
import os.path as osp
import os
from datetime import datetime as dt
import csv
import re


log = utils.get_logger()


def manifest(imgdir, ext=None):
    '''
    Does:
        - Generates a generic manifest in the specified image directory.
        - Fields are an id in the format [date]-[time]-[filenumber] and
          the filename.

    Args
        - imgdir: str
            -desc: image directory for which to generate manifest
        - ext: str
            -desc: File extension of images for which to generate the manifest
    Returns:
        None

    Notes:
        - Supported image types: [ tiff, jpg, png ] - can easily append
    '''
    if not osp.isdir(imgdir):
        log.error("Image directory '{}' does not exist"
                  .format(imgdir))

    log.info("Manifest being generated with fields: [ id, filename ]")
    mfile = open(osp.join(imgdir, 'manifest.csv'), 'r')
    writer = csv.writer(mfile)
    writer.writerow(["id", "filename"])

    idtag = dt.now().strftime("%m%d%y-%H%M%S")

    if not ext:
        PATTERN = re.compile(r".*\.(jpg|png|tiff)")
    elif ext == 'jpg':
        PATTERN = re.compile(r".*\.jpg")
    elif ext == 'png':
        PATTERN = re.compile(r".*\.png")
    elif ext == 'tiff':
        PATTERN = re.compile(r".*\.tiff")

    img_c = 0
    for id, filename in enumerate(os.listdir(imgdir)):
        if PATTERN.match(filename):
            writer.writerow(["{}-{:04d}".format(idtag, id),
                             osp.join(imgdir, filename)])
            img_c += 1
        if img_c == 9999:
            log.warning("Zooniverse's default limit of subjects per"
                        + " user is 9999. You may not be able to load"
                        + " this entire subject set.")
            if not utils.get_yn("Continue adding images to manifest?"):
                break
            img_c += 1

    log.info("DONE: {} subjects written to manifest"
             .format(img_c))

    mfile.close()
    return True
