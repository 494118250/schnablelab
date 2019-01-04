from getpass import getpass
import sys
import os.path as osp
import os
from datetime import datetime as dt
import csv
import logging
import re
from subprocess import run, CalledProcessError
from pprint import pprint
try:
    import panoptes_client as pan
    from panoptes_client.panoptes import PanoptesAPIException
except ImportError:
    print("panoptes_client package could not be imported. To install use:")
    print("> pip install panoptes-client")
    print("Or activate your panoptes-client enabled environment")
    exit(False)


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.FileHandler(__name__ + '.log'))
log.info('### EXECUTION DATE TIME: ' + dt.now().isoformat() + ' ###')
log.addHandler(logging.StreamHandler())

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
            subject_set = pan.SubjectSet.find(opts.subject)
        except PanoptesAPIException as e:
            log.error("Could not find subject set id")
            for arg in e.args:
                log.error("> " + arg)
            return False
    else:
        log.info("Creating new subject set")
        subject_set = pan.SubjectSet()
        subject_set.links.project = project

        while(True):
            name = input("Enter subject set display name: ")
            try:
                subject_set.display_name = name
                subject_set.save()
            except PanoptesAPIException as e:
                log.error("Could not set subject set display name")
                for arg in e.args:
                    if arg == 'You must be logged in to access this resource.':
                        log.error("User credentials invalid")
                        exit(False)
                    log.error("> " + arg)
                    if arg == 'Validation failed:' \
                              + ' Display name has already been taken':
                        log.info("To use {} as the display name,"
                                 + " get the subject set id from zooniverse"
                                 + " and call this command with --subject <id>")
                        if not utils.get_yn('Try again?'):
                            exit(False)
                continue

            break

    # NOTE: This would need to be cross-platform and efficient
    #       I am removing this feature and leaving file compression to
    #       the user.
    '''
    if opts.convert:
        log.info("Compressing and converting to jpg")
        log.critical("Warning: All jpg files will be overwritten.")

        if utils.get_yn("Continue?"):
            utils.convert(imgdir)
    '''

    if not osp.isfile(osp.join(imgdir, 'manifest.csv')):
        log.info("Generating manifest")
        if opts.extension:
            mani_gen_succeeded = manifest(imgdir, ext=opts.extension)
        else:
            mani_gen_succeeded = manifest(imgdir)
        if not mani_gen_succeeded:
            log.error("Could not upload images, no manifest.")
            return False

    mfile = open(osp.join(imgdir, 'manifest.csv'), 'r')
    fieldnames = mfile.readline().strip().split(",")
    mfile.seek(0)
    reader = csv.DictReader(mfile)

    if 'filename' not in fieldnames:
        log.error("Manifest file must have a 'filename' column")
        return False

    log.info("Loading images from manifest...")
    error_count = 0
    success_count = 0
    project.reload()

    for row in reader:
        try:

            # Check file size
            filesize = osp.getsize(row['filename'])
            if filesize > 256000:
                log.warning("File size of {}K is larger than recommended 256K"
                         .format(filesize))

            temp_subj = pan.Subject()
            temp_subj.add_location(row['filename'])
            temp_subj.metadata.update(row)
            temp_subj.links.project = project
            temp_subj.save()
            subject_set.add(temp_subj)
        except PanoptesAPIException as e:
            error_count += 1
            log.error("Error on row: {}".format(row))
            for arg in e.args:
                log.error("> " + arg)
            continue

        success_count += 1
        log.debug("{}- {} - success"
                .format(success_count,
                        str(osp.basename(row['filename']))))

    log.info("Upload completed at: " + dt.now().strftime("%H:%M:%S %m/%d/%y"))

    log.info("{} of {} images loaded".format(success_count,
                                             success_count + error_count))

    log.info("Remember to link your workflow to this subject set")

    return True


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
        return False

    log.info("Manifest being generated with fields: [ id, filename ]")
    mfile = open(osp.join(imgdir, 'manifest.csv'), 'w')
    writer = csv.writer(mfile, lineterminator='\n')
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

    if img_c == 0:
        log.warning("No images found in imgdir")
    else:
        log.info("DONE: {} subjects written to manifest"
                 .format(img_c))

    mfile.close()
    return True


def export(projid, outfile_path, opts):
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

    project = utils.connect(projid)
    export = utils.get_export(project, type=opts.type)

    if not osp.exists(osp.dirname(outfile_path)):
        log.error("Image directory '{}' does not exist"
                  .format(imgdir))
        return False

    with open(outfile_path, 'w') as zoof:
        zoof.write(export.text)

    return True


class utils:

    def get_export(project, type='classifications'):
        try:
            log.info("Getting export, this may take some time...")
            export = project.get_export(type)
        except PanoptesAPIException as e:
            log.error("Error getting export")
            for arg in e.args:
                log.error("> " + arg)
            return False

        return export


    def convert(imgdir, ext=None):
        ''' Image compression and conversion to jpg '''

        cmd = ["mogrify", "-strip", "-quality", "85%", "-format", "jpg"]
        try:
            if ext:
                cmd = cmd.append("*." + ext)
            else:
                cmd.append([osp.join(imgdir, "*.jpg"),
                            osp.join(imgdir, "*.png"),
                            osp.join(imgdir, "*.tiff")])
            proc_ret = run(cmd, shell=bash)
        except CalledProcessError as e:
            log.error("Failed to compress images")
            pprint(e)

        pprint(proc_ret)
        return True


    def connect(projid, **kwargs):
        ''' Override of panoptes connect method '''

        if 'un' in kwargs and 'pw' in kwargs:
            un = kwargs['un']
            pw = kwargs['pw']
        else:
            un = input("Enter zooniverse username: ")
            pw = getpass()
        try:
            pan.Panoptes.connect(username=un, password=pw)
            project = pan.Project.find(id=projid)
        except PanoptesAPIException as e:
            log.error("Could not connect to zooniverse project")
            for arg in e.args:
                log.error("> " + arg)
            raise

        return project


    def get_yn(message):
        while True:
            val = input(message + " [y/n] ")
            if val.lower() in ['y', 'n']:
                return True if val.lower() == 'y' else False
            else:
                print("Invalid input")
