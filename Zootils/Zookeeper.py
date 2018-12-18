# -*- coding: UTF-8 -*-

"""
Upload images to zooniverse project
"""
from getpass import getpass
from JamesLab.apps.base import ActionDispatcher, OptionParser
import sys
import os.path as osp
import os
from datetime import datetime as dt
import csv
import logging
import re
from subprocess import run, CalledProcessError
from pprint import pprint


'''
Set logging objects
'''
log = logging.getLogger('zookeeper')

log.setLevel(logging.DEBUG)
# For outputting logs to files
log.addHandler(logging.FileHandler('zoo_load.err'))
# for output to stdout and stderr
log.addHandler(logging.StreamHandler())


try:
    from panoptes_client import Panoptes, Project, SubjectSet
    from panoptes_client.panoptes import PanoptesAPIException
except ImportError:
    log.info("panoptes_client package could not be imported. To install use:")
    log.info("> pip install panoptes-client")
    log.info("Or activate your panoptes-client enabled environment")
    exit(False)


def main():
    actions = (
        ('upload', 'load images to zooniverse'),
        ('export', 'Get annotation and other exports'),
        ('manifest', 'Generate a manifest for zooniverse subject set upload')
    )
    p = ActionDispatcher(actions)
    p.dispatch(globals())


def manifest(args):
    '''
    %prog manifest imgdirectory

    Does:
        Generates a manifest inside the specified image directory.

    Args:
        ~: imgdir
            -type: str
            -desc: The image directory in which to generate the manifest.
    Returns:
        None
    '''
    p = OptionParser(manifest.__doc__)

    opts, args = p.parse_args(args)

    if len(sys.argv) != 1:
        exit(not p.print_help())

    imgdir = args[1]

    __generate_manifest(imgdir)
    return


def upload(imgdir, projid, opts=None, **kwargs):
    '''
    %prog upload imgdir zoo_proj_id

    Does:
        - Uploads images from the specified image directory to zooniverse
          project specified by zoo_project_id.
        - Will also generate a manifest if one is not already present inside
          imgdir.

    Note:
        - If using a custom manifest

    Args:
        - imgdir
            -type: str
            -desc: The directory of the images to be uploaded
        - proj_id
            -type: str
            -desc: The zooniverse project id to upload the images to.
    Returns:
        None
    '''

    if opts.quiet:
        log.setLevel(logging.INFO)

    if not osp.isdir(imgdir):
        log.error("Image directory '{}' does not exist".format(imgdir))
        return False

    try:
        project = __connect_zoo(projid)
    except PanoptesAPIException:
        exit(False)

    if not opts.subject and 'subjsetid' not in kwargs:
        log.info("Creating new subject set")
        subject_set = SubjectSet()
        subject_set.links.project = project

        if dispname:
            name = dispname

        while(True):

            name = input("Enter subject set display name: ")

            try:
                subject_set.display_name = name
                subject_set.save()

            except pan.panoptes.PanoptesAPIException as e:
                log.error("Could not set subject set display name")
                for arg in e.args:
                    log.error("> " + arg)
                continue

            break

    else:
        try:
            if opts.subject:
                subject_set = pan.SubjectSet.find(opts.subject)
            else:
                subject_set = pan.SubjectSet.find(subjsetid)
        except pan.panoptes.PanoptesAPIException as e:
            log.error("Could not find subject set id")
            for arg in e.args:
                log.error("> " + arg)
            exit(False)

    mani_exists = osp.isfile(osp.join(imgdir, 'manifest.csv'))

    if opts.convert:
        log.info("Compressing and converting to jpg")
        if mani_exists:
            log.warning("If using a custom manifest, image filenames must"
                        + " use .jpg extension.")

        __convert(imgdir)

    if not mani_exists:
        log.info("Generating manifest")
        if opts.convert:
            __generate_manifest(imgdir, ext='jpg')
        else:
            __generate_manifest(imgdir)

    mfile = open(osp.join(imgdir, 'manifest.csv'), 'r')
    fieldnames = mfile.readline().strip().split(",")
    mfile.seek(0)
    reader = csv.DictReader(mfile)

    if 'filename' not in fieldnames:
        log.error("Manifest file must have a 'filename' column")
        exit(False)

    log.info("Loading images fom manifest.")
    error_count = 0
    success_count = 0
    project.reload()

    for row in reader:
        try:
            curr_subj = pan.Subject()
            curr_subj.add_location(row['filename'])
            curr_subj.metadata.update(row)
            curr_subj.save()
            subject_set.add(curr_subj)
        except pan.panoptes.PanoptesAPIException as e:
            error_count += 1
            log.error("Error on row: {}".format(row))
            for arg in e.args:
                log.error("> " + arg)
            continue

        success_count += 1
        log.log(1, "{}- {} - success."
                .format(success_count,
                        osp.basename(row['filename'])))

    log.info("Upload completed at {}".format(
        dt.now().strftime("%m/%s/%y %H:%M:%S")))

    log.info("{} of {} images loaded".format(success_count,
                                             success_count + error_count))

    if opts.workflow:
        pan.workflow.Workflow().find(opts.workflow)
    else:
        log.info("Remember to link your workflow to this subject set")

    return True


# UNTESTED
def export(args):
    '''
    %prog export project_id output_dir

    Does:
        Fetches export from zooniverse for specified project.

    Args:
        - project_id
            -type: str
            -desc: The zooniverse project id
        - output_dir
            -type: str
            -desc: Path to the image directory with images to be uploaded
    Returns:
        None
    '''
    p = OptionParser(upload.__doc__)
    p.add_option('-t', '--type', default='classifications',
                 help='specify the type of export')

    opts, args = p.parse_args(args)

    if len(args) != 2:
        exit(not p.print_help())

    proj_id, output_dir = args

    if not osp.isdir(output_dir):
        log.error("Output directory does not exist")
        raise OSError("{} does not exist".format(output_dir))

    project = __connect_zoo(proj_id)

    try:
        log.info("Getting export, this may take some time.")
        export = project.get_export(opts.type)
        fname = "zoo_export.{}.csv".format(
                dt.now().strftime('%b-%d-%G-%I%:M%p'))
        with open(osp.join(output_dir, fname), 'w') as zoof:
            zoof.write(export)
    except pan.panoptes.PanoptesAPIException as e:
        log.error("Error getting export: {}".format(e.args))
        exit(False)


'''
HELPER FUNCTIONS
'''


def __convert(imgdir):

    cmd = ["mogrify", "-strip", "-quality", "85%", "-format", "jpg"]

    try:
        proc_ret = run(cmd.append([osp.join(imgdir, "*.jpg"),
                                   osp.join(imgdir, "*.png"),
                                   osp.join(imgdir, "*.tiff")]),
                       capture_output=True)
    except CalledProcessError as e:
        log.error("Failed to compress images")
        pprint(e)

    pprint(proc_ret)

    return


def __generate_manifest(imgdir, ext=None):
    '''
    Does:
        Generates a generic manifest in the specified image directory.
        Fields are an id in the format [date]-[time]-[filenumber] and
        the filename.

    Args
        - imgdir
            -type: str
            -desc: image directory for which to generate manifest
        - return_handle
            -type: bool
            -desc: Whether to return open file handle to the new manifest
    Returns:
        If return_handle is True
        --> file handle to new manifest
        Else
        --> None

    Notes:
        - Supported image types: [ tiff, jpg, png ] - can easily append
    '''

    if not osp.isdir(imgdir):
        log.error("Directory '{}' does not exist".format(imgdir))

    log.info("Manifest being generated with fields: [ id, filename ]")

    mfile = open(osp.join(imgdir, 'manifest.csv'), 'w+')
    idtag = dt.now().strftime("%m%d%y-%H%M%S")
    writer = csv.writer(mfile)
    writer.writerow(["id", "filename"])

    # Insert "|<img_file_pattern>" for additional image types
    if not ext:
        PATTERN = re.compile(r".*\.jpg")
    else:
        PATTERN = re.compile(r".*\.(jpg|png|tiff)")

    img_count = 0

    for id, filename in enumerate(os.listdir(imgdir)):
        if PATTERN.match(filename):
            writer.writerow(["{}-{:04d}".format(idtag, id),
                             osp.join(imgdir, filename)])
            img_count += 1
        if img_count == 9999:
            log.warning("Zooniverse's default limit of subjects per user is"
                        + " 9999. You may not be able to load this entire"
                        + " subject set.")
            if not __get_yn("Continue?"):
                break
            img_count += 1

    log.info("{} subjects written to manifest.".format(img_count))

    mfile.close()
    return


def __connect_zoo(proj_id, un=None, pw=None):
    '''
    Does:
        Connects to the zooniverse through the panoptes api
        and gets an instance of the project.

    Args:
        - proj_id
            -type: str
            -desc: The zooniverse project id
    Returns:
        - proj
            -type: obj - panoptes_client.Project.project
            -desc: and instance of the zooniverse project

    Raises:
        PanoptesAPIException
    '''
    un = input("Enter zooniverse username: ")
    pw = getpass()

    try:
        pan.Panoptes.connect(username=un, password=pw)
        project = pan.Project.find(id=proj_id)
    except pan.panoptes.PanoptesAPIException as e:
        log.error("Could not connect to zooniverse project")
        for arg in e.args:
            log.error("> " + arg)
        raise

    return project


def __get_yn(message):
    while True:
        val = input(message + " [y/n]")
        if val.lower() in ['y', 'n']:
            return True if val.lower() == 'y' else False
        else:
            print("Invalid input")


if __name__ == '__main__':
    main()
