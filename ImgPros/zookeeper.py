# -*- coding: UTF-8 -*-

"""
Upload images to zooniverse project
"""
from getpass import getpass
from JamesLab.apps.base import ActionDispatcher, OptionParser
import pickle as pkl
import sys
import os
from glob import glob
from datetime import datetime as dt
import csv
import logging
import json
from pprint import pprint
import re


log=logging.getLogger('zookeeper')
log.setLevel(logging.DEBUG)
log.addHandler(logging.FileHandler('zoo_load.err'))
log.addHandler(logging.StreamHandler())

try:
    import panoptes_client as pan
except ImportError:
    log.info("panoptes_client package could not be imported. To install use:")
    log.info("> pip install panoptes-client")
    log.info("Or activate your panoptes-client enabled anaconda environment")
    quit()


def main():
    actions = (
        ('upload', 'load images to zooniverse'),
        ('export', 'Get annotation and other exports'),
        ('retire', 'Retire subjects that have been'),
        ('manifest', 'Generate a manifest for zooniverse subject set upload')
    )
    p = ActionDispatcher(actions)
    p.dispatch(globals())


def retire(args):
    raise NotImplementedError


def manifest(args):
    p = OptionParser(manifest.__doc__, usage="Generate a manifest for "
        + "zooniverse subject set upload.")
    raise NotImplementedError


# UNTESTED
def upload(args, un=None, pw=None, dispname=False):
    """
    %prog upload img_directory zoo_project_id
    """
    p = OptionParser(upload.__doc__)
    p.add_option('-s', '--subject', default=False,
        help='Designate a subject set id')
    p.add_option('-q', '--quiet', default=False,
        help='Silences output when uploading images to zooniverse.')
    p.add_option('-w', '--workflow', default=None,
        help='Designate a workflow id to link to this subject set')
    # TODO: ??
    p.add_option('-c', '--convert', default=False,
        help='Compress and convert files to jpg for faster load times on zooniverse.\n'\
            +'Command: magick -strip -interlace Plane -quality 85% -format jpg <img_directory>/<filename>.png')

    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())

    img_dir, proj_id = args

    if opts.quiet:
        log.setLevel(logging.ERROR)

    if not os.path.isdir(img_dir):
        log.info("{} is not a valid path".format(img_dir))
        return

    if not un and not pw:
        un, pw, sc = __get_zoo_credentials()
    else:
        sc = False

    try:
        log.info("Logging in as {}".format(un))
        pan.Panoptes.connect(username=un, password=pw)
        pprint(pan.user.User())

        if sc:
            __save_creds(un, pw)

        subjdat = None

        project = pan.Project.find(id=proj_id)
        if opts.subject:
            subject_set = pan.SubjectSet.find(opts.subject)
        else:
            log.info("Creating new subject set")
            subject_set = pan.SubjectSet()
            print(subject_set)
            subject_set.links.project = project
            if not dispname:
                dispname = input("Enter subject set display name: ")
            try:
                subject_set.display_name = dispname
                subjdat = subject_set.save()

            except pan.panoptes.PanoptesAPIException as e:
                log.info("Subject set display name already taken")
                if not dispname:
                    quit()
                else:
                    raise


    except pan.panoptes.PanoptesAPIException as e:
        log.error("PanoptesAPIException: {}".format(e))
        raise

    if not os.path.isfile(os.path.join(img_dir, 'manifest.csv')):
        log.info("There is no manifest, one will be generated.")
        with __generate_manifest(img_dir) as mfile:
            reader = csv.DictReader(mfile)

    else:
        with open(os.path.join(img_dir, 'manifest.csv'), 'r') as mfile:
            reader = csv.DictReader(mfile)

    fieldnames = reader.fieldnames()
    if 'filename' not in fieldnames:
        log.info("Manifest file must have a filename field")
        quit()

    project.reload()

    log.info("Loading images, all errors will be logged in ./zoo_load.err")

    for row in reader:
        if not opts.quiet:
            log.info("Loading {}".format(row['filename']))
        try:
            curr_subj = pan.Subject()
            curr_subj.add_location(row['filename'])
            curr_subj.metadate.update(row)
            curr_subj.save()
            subject_set.add(curr_subj)
        except pan.panoptes.PanoptesAPIException as e:
            log.error("Error on row:\n>> {}".format(row))

    log.info("Upload completed at {}".format(
        dt.now().strftime("%m/%s/%y %H:%M:%S")))

    if opts.workflow:
        pan.workflow.Workflow().find(opts.workflow)
    else:
        log.info("Because you did not specify a workflow, you will need to link"
            + " your subject set to a workflow.")

# UNTESTED
def export(args):
    """
    %prog export project_id output_dir

    Get classifications or other export
    """
    p = OptionParser(upload.__doc__)
    p.add_option('-t', '--type', default='classifications',
                help='specify the type of export')

    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())

    proj_id, output_dir = args

    if not os.path.isdir(output_dir):
        log.info("Output directory does not exist")
        quit()

    un, pw, sc = __get_zoo_credentials()

    try:
        pan.Panoptes.connect(username=un, password=pw)
        project = pan.Project.find(id = proj_id)
        pprint(pan.user.User())
    except pan.panoptes.PanoptesAPIException as e:
        log.error("Could not connect: {}".format(e))
        raise
    try:
        log.info("Getting export, this may take some time.")
        export = project.get_export(opts.type)
        with open(os.path.join(output_dir, \
            "zoo_export.{}.csv".format(dt.now().strftime('%b-%d-%G-%I%:M%p')),
            'w')) as zoof:
            zoof.write(export)
    except pan.panoptes.PanoptesAPIException as e:
        log.error("Error getting export: {}".format(e))
        raise

# UNTESTED
def __generate_manifest(img_dir):

    log.info("Manifest being generated with fields: [ id, filename ]")

    # get all files that are png or jpg
    idtag = dt.now().strftime("%m%d%y-%H%M%S")
    mfile = open(os.path.join(img_dir, 'manifest.csv'), 'w+')

    count = 0
    writer = csv.writer(mfile)
    writer.writerow(["id","filename"])

    PATTERN = re.compile(".*\.(jpg|png)")

    for id, filename in enumerate(os.listdir(img_dir)):
        if PATTERN.match(filename):
            writer.writerow(["{}-{:04d}".format(idtag, id), filename])
            count += 1
        if count >= 9999:
            log.info("This upload is too big, limit is 9999 images.")
            break

    log.info("Manifest generated for {} files.".format(count))

    return mfile

"""
Private functions:
"""

# UNTESTED
def __get_zoo_credentials():
    if not os.path.exists("./.zoo.pkl"):
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


def __get_new_user_creds():

    un = input("Enter zooniverse username: ")
    pw = getpass()

    if input("Would you like to save your credentials if valid? (y/n) ") \
        in ['y', 'Y']:
        sc = True
    else:
        sc = False

    return un, pw, sc


def __save_creds(un, pw):

    log.info("Saving credentials")

    if os.path.exists(os.path.join(os.path.expanduser("~"), ".zoo")):
        with open(os.path.join(os.path.expanduser("~"), ".zoo", 'rb+')) as pfile:
            creds = json.load(pfile)
            creds[un] = pw
            json.dump(creds, pfile)
    else:
        with open(os.path.join(os.path.expanduser("~"), ".zoo", 'wb')) as pfile:
            json.dump(creds, pfile)


if __name__ == '__main__':
    main()
