# -*- coding: UTF-8 -*-

"""
Upload images to zooniverse project
"""
from getpass import getpass
from JamesLab.apps.base import ActionDispatcher, OptionParser
import sys
import os.path as osp
import os
import errno
from datetime import datetime as dt
import csv
import logging
import re
import OSError


'''
Set logging objects
'''
log = logging.getLogger('zookeeper')
log.setLevel(logging.DEBUG)
log.addHandler(logging.FileHandler('zoo_load.err'))
log.addHandler(logging.StreamHandler())


try:
    import panoptes_client as pan
except ImportError:
    log.info("panoptes_client package could not be imported. To install use:")
    log.info("> pip install panoptes-client")
    log.info("Or activate your panoptes-client enabled environment")
    quit()


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
    %prog manifest img_directory

    Does:
        Generates a manifest inside the specified image directory.

    Args:
        ~: img_dir
            -type: str
            -desc: The image directory in which to generate the manifest.
    Returns:
        None
    '''
    p = OptionParser(manifest.__doc__)

    opts, args = p.parse_args(args)

    if len(sys.argv) != 1:
        exit(not p.print_help())

    img_dir = args[1]

    try:
        __generate_manifest(img_dir, return_handle=False)
    except OSError as e:
        if e.errno == errno.ERNOENT:
            log.error("Image directory did not exist")
        else:
            lor.error("Could not generate manifest file: {}".format(e))
        exit(-1)


def upload(args, un=None, pw=None, dispname=None, subjsetid=None):
    '''
    %prog upload img_dir zoo_proj_id

    Does:
        Uploads images from the specified image directory to zooniverse
        project specified by zoo_project_id. This function will also
        generate a manifest if one is not already present inside img_dir.

    Args:
        ~: img_dir
            -type: str
            -desc: The directory of the images to be uploaded
        ~: proj_id
            -type: str
            -desc: The zooniverse project id to upload the images to.
    Returns:
        None

    '''
    p = OptionParser(upload.__doc__)
    p.add_option('-s', '--subject', default=False,
                 help='Designate a subject set id')
    p.add_option('-q', '--quiet', default=False,
                 help='Silences output when uploading images to zooniverse.')
    p.add_option('-w', '--workflow', default=None,
                 help='Designate a workflow id to link to this subject set')
    # TODO: ??
    p.add_option('-c', '--convert', default=False,
                 help="Compress and convert files to jpg for faster load times"
                 + " on zooniverse.\n"
                 + " Command: magick -strip -interlace Plane -quality 85%"
                 + " -format jpg <img_directory>/<filename>.png")

    opts, args = p.parse_args(args)

    if len(args) != 2:
        exit(not p.print_help())

    img_dir, proj_id = args

    if opts.quiet:
        log.setLevel(logging.ERROR)

    try:
        __check_dir(img_dir)
    except OSError as e:
        if e.errno == errno.ENOENT:
            log.error("Could not find image directory")
            exit(-1)
        else:
            log.error("Error checking image directory: {}".format(e))

    try:
        project = __connect_zoo(proj_id)
    except pan.panoptes.PanoptesAPIException:
        exit(-1)

    if not opts.subject and not subjsetid:
        log.info("Creating new subject set")
        subject_set = pan.SubjectSet()
        subject_set.links.project = project

        if not dispname:
            dispname = input("Enter subject set display name: ")

        try:
            subject_set.display_name = dispname
            subject_set.save()

        except pan.panoptes.PanoptesAPIException as e:
            log.error("Subject set display name already taken")
            if not dispname:
                quit()
            raise

    else:
        try:
            if opts.subject:
                subject_set = pan.SubjectSet.find(opts.subject)
            else:
                subject_set = pan.SubjectSet.find(subjsetid)
        except pan.panoptes.PanoptesAPIException as e:
            log.error("Could not find subject set id")
            raise

    if osp.isfile(osp.join(img_dir, 'manifest.csv')):
        with open(osp.join(img_dir, 'manifest.csv'), 'r') as mfile:
            reader = csv.DictReader(mfile)
    else:
        log.info("There is no manifest, one will be generated.")
        mfile = __generate_manifest(img_dir)
        mfile.close()

        ''' Would this work?
        with __generate_manifest(img_dir) as mfile:
            reader = csv.DictReader(mfile)
        '''

    fieldnames = reader.fieldnames()
    if 'filename' not in fieldnames:
        log.info("Manifest file must have a 'filename' column")
        exit(-1)

    project.reload()

    log.info("Loading images, all errors will be logged in ./zoo_load.err")

    for row in reader:
        if not opts.quiet:
            log.info("Loading {}".format(row['filename']))
        try:
            curr_subj = pan.Subject()
            curr_subj.add_location(row['filename'])
            curr_subj.metadata.update(row)
            curr_subj.save()
            subject_set.add(curr_subj)
        except pan.panoptes.PanoptesAPIException as e:
            log.error("Error on row:\n>> {}".format(row))

    log.info("Upload completed at {}".format(
        dt.now().strftime("%m/%s/%y %H:%M:%S")))

    if opts.workflow:
        pan.workflow.Workflow().find(opts.workflow)
    else:
        log.info("Because you did not specify a workflow, you will need to"
                 + " link your subject set to a workflow.")


# UNTESTED
def export(args):
    '''
    %prog export project_id output_dir

    Does:
        Fetches export from zooniverse for specified project.

    Args:
        ~: project_id
            -type: str
            -desc: The zooniverse project id
        ~: output_dir
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
        exit(-1)


'''
HELPER FUNCTIONS
'''


def __check_dir(dir):
    if osp.exists(dir):
        return True
    log.error("Directory {} does not exist".format(dir))
    return False

def __generate_manifest(img_dir, return_handle=True):
    '''
    Does:
        Generates a generic manifest in the specified image directory.
        Fields are an id in the format [date]-[time]-[filenumber] and
        the filename.

    Args
        ~: img_dir
            -type: str
            -desc: image directory for which to generate manifest
        ~: return_handle
            -type: bool
            -desc: Whether to return open file handle to the new manifest
    Returns:
        If return_handle is True
        --> file handle to new manifest
        Else
        --> None

    Notes:
        Supported image types: [ tiff, jpg, png ] - can easily append
    '''

    __check_dir(img_dir)


    log.info("Manifest being generated with fields: [ id, filename ]")

    mfile = open(osp.join(img_dir, 'manifest.csv'), 'w+')
    idtag = dt.now().strftime("%m%d%y-%H%M%S")
    writer = csv.writer(mfile)
    writer.writerow(["id", "filename"])

    # Insert "|<img_file_pattern>" for additional image types
    PATTERN = re.compile(r".*\.(jpg|png|tiff)")
    img_count = 0

    for id, filename in enumerate(os.listdir(img_dir)):
        if PATTERN.match(filename):
            writer.writerow(["{}-{:04d}".format(idtag, id), filename])
            img_count += 1
        if img_count == 9999:
            log.warning("Zooniverse's default limit of subjects per user is"
                        + " 9999. You may not be able to load this entire"
                        + " subject set.")
            if not __get_yn("Continue?"):
                break
            img_count += 1

    log.info("{} subjects written to manifest".format(img_count))

    if return_handle:
        return mfile.seek(0)
    else:
        mfile.close()
        return None


def __connect_zoo(proj_id, un=None, pw=None):
    '''
    Does:
        Connects to the zooniverse through the panoptes api
        and gets an instance of the project.

    Args:
        ~: proj_id
            -type: str
            -desc: The zooniverse project id
    Returns:
        ~:proj
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
        log.error("Could not complete connection to zooniverse: {}"
                  .format(e.args))
        raise
    return project


def __get_yn(message):
    while True:
        val = input(message + " [y/n]")
        if val.lower() in ['y', 'n']:
            return True if val.lower() == 'y' else False
        else:
            print("Invalid input")


### GOLD PLATING FEATURE DUMP ###
'''
DECIDED THAT ZOONIVERSE WRAPPER WASN'T A GOOD PLACE TO IMPLEMENT
FULL FEATURED CREDENTIAL MANAGEMENT SOFTWARE

def __save_creds(un, pw):

    log.info("Saving credentials")

    if osp.exists(osp.join(osp.expanduser("~"), ".zoo")):
        with open(osp.join(osp.expanduser("~"), ".zoo", 'rb+')) as pfile:
            creds = json.load(pfile)
            creds[un] = pw
            json.dump(creds, pfile)
    else:
        with open(osp.join(osp.expanduser("~"), ".zoo", 'wb')) as pfile:
            json.dump(creds, pfile)

def __get_zoo_credentials():
    if not osp.exists("./.zoo.pkl"):
        return __get_new_user_creds()
    elif input("Used saved login credentials? (y/n)") == 'y':
        with open("./.zoo.pkl", 'rb') as usersfile:
            users = pkl.load(usersfile)

            # users credentials dict empty
            if not users:
                return __get_new_user_creds()

            print("Available user credentials: ")
            print("{:3d} - {}".format(0, 'other'))
            for i, user in enumerate(list(users.keys())):
                print("{:3d} - {}".format(i+1, user))
            while True:
                ind = input("Which username? ")
                if not ind.isdigit(): continue
                if int(ind) < 0 or int(ind) > len(users.keys()):
                    print("Invalid Entry")
                elif ind == '0':
                    return __get_new_user_creds()
                else:
                    un = list(users.keys())[int(ind)-1]
                    pw = users[un]
                    return un, pw, None

    return __get_new_user_creds()
'''

if __name__ == '__main__':
    main()
