import os.path as osp
from datetime import datetime as dt
import csv
import logging
from JamesLab.Zootils import utils
try:
    from panoptes_client import (
                                 SubjectSet,
                                 workflow,
                                 Subject
                                )
    from panoptes_client.panoptes import PanoptesAPIException
except ImportError:
    print("panoptes_client package could not be imported. To install use:")
    print("> pip install panoptes-client")
    print("Or activate your panoptes-client enabled environment")
    exit(False)


log = utils.get_logger()


def upload(imgdir, projid, opts, **kwargs):
    '''
    %prog upload imgdir zoo_proj_id
    Does:
        - Uploads images from the specified image directory to zooniverse
          project specified by zoo_project_id.
        - Will also generate a manifest if one is not already present inside
          imgdir.
    Note:
        - This program uploads only images listed in the manifest.csv file.
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
        project = utils.connect(projid)
    except PanoptesAPIException:
        return False

    if opts.subject:
        try:
            subject_set = SubjectSet.find(opts.subject)
        except PanoptesAPIException as e:
            log.error("Could not find subject set id")
            for arg in e.args:
                log.error("> " + arg)
            return False
    else:
        log.info("Creating new subject set")
        subject_set = SubjectSet()
        subject_set.links.project = project

        while(True):

            name = input("Enter subject set display name: ")

            try:
                subject_set.display_name = name
                subject_set.save()

            except PanoptesAPIException as e:
                log.error("Could not set subject set display name")
                for arg in e.args:
                    log.error("> " + arg)
                continue

            break

    if opts.convert:
        log.info("Compressing and converting to jpg")
        log.critical("Warning: All jpg files will be overwritten.")

        if utils.get_yn("Continue?"):
            utils.convert(imgdir)

    if not osp.isfile(osp.join(imgdir, 'manifest.csv')):
        log.info("Generating manifest")
        if opts.convert:
            utils.manifest(imgdir, ext='jpg')
        else:
            utils.manifest(imgdir)

    mfile = open(osp.join(imgdir, 'manifest.csv'), 'r')
    fieldnames = mfile.readline().strip().split(",")
    mfile.seek(0)
    reader = csv.DictReader(mfile)

    if 'filename' not in fieldnames:
        log.error("Manifest file must have a 'filename' column")
        return False

    log.info("Loading images fom manifest.")
    error_count = 0
    success_count = 0
    project.reload()

    for row in reader:
        try:
            temp_subj = Subject()
            temp_subj.add_location(row['filename'])
            temp_subj.metadata.update(row)
            temp_subj.save()
            subject_set.add(temp_subj)
        except PanoptesAPIException as e:
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
        workflow.Workflow().find(opts.workflow)
    else:
        log.info("Remember to link your workflow to this subject set")

    return True
