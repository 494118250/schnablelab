# -*- coding: UTF-8 -*-

"""
Upload images to zooniverse project
"""
from getpass import getpass
from JamesLab.apps.base import ActionDispatcher, OptionParser
import pickle as pkl
import sys
import os.path as osp
import os
from datetime import datetime as dt
import csv
import logging
from pprint import pprint
import re


'''
New concepts:
'''
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
        ('manifest', 'Generate a manifest for zooniverse subject set upload')
    )
    p = ActionDispatcher(actions)
    p.dispatch(globals())


def manifest(args):
    p = OptionParser(manifest.__doc__, usage="Generate a manifest for"
        + " zooniverse subject set upload.")
    raise NotImplementedError


def upload(args, un=None, pw=None, dispname=None, subjsetid=None):
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

    if not osp.isdir(img_dir):
        log.error("{} is not a valid path".format(img_dir))
        quit()
        
    un, pw = __get_zoo_creds()

    try:
        log.info("Logging in...")
        pan.Panoptes.connect(username=un, password=pw)
        project = pan.Project.find(id=proj_id)
    except pan.panoptes.PanoptesAPIException as e:
        log.error("Either the credentials were wrong or"
                  + " the project id does not exist:")
        log.error("PanoptesAPIException: {}".format(e))
        raise

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


def __generate_manifest(img_dir):

    log.info("Manifest being generated with fields: [ id, filename ]")

    # get all files that are png or jpg
    idtag = dt.now().strftime("%m%d%y-%H%M%S")

    img_count = 0

    mfile = open(osp.join(img_dir, 'manifest.csv'), 'w+')

    writer = csv.writer(mfile)
    writer.writerow(["id", "filename"])

    PATTERN = re.compile(".*\.(jpg|png|tiff)")

    for id, filename in enumerate(os.listdir(img_dir)):
        if PATTERN.match(filename):
            writer.writerow(["{}-{:04d}".format(idtag, id), filename])
            img_count += 1
        if img_count == 9999:
            log.warning("Zooniverse's default limit for subjects per user is"
                        + " 9999. You may not be able to load the entire "
                        + " subject set.")
            if not __get_yn("Continue?"):
                break
            img_count += 1

    log.info("{} subjects written to manifest".format(img_count))
    return mfile.seek(0)

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

    if not osp.isdir(output_dir):
        log.info("Output directory does not exist")
        quit()

    un, pw = __get_zoo_creds()

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
        with open(osp.join(output_dir, \
            "zoo_export.{}.csv".format(dt.now().strftime('%b-%d-%G-%I%:M%p')),
            'w')) as zoof:
            zoof.write(export)
    except pan.panoptes.PanoptesAPIException as e:
        log.error("Error getting export: {}".format(e))
        raise




def __get_yn(message):
    while True:
        val = input(message + " [y/n]")
        if val.lower() in ['y', 'n']:
            return True if val.lower() == 'y' else False
        else:
            print("Invalid input")


def __get_zoo_creds():

    un = input("Enter zooniverse username: ")
    pw = getpass()

    return un, pw


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
