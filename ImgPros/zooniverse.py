# -*- coding: UTF-8 -*-

"""
Upload images to zooniverse project
"""
from getpass import getuser, getpass
import importlib
from JamesLab.apps.base import ActionDispatcher, OptionParser
import pickle as pkl
import sys
import os
import traceback as tb
from glob import glob
from datetime import datetime as dt
import csv

try:
    from panoptes_client import exportable, panoptes, Panoptes, user, Project, SubjectSet, Subject
except ImportError:
    print("panoptes_client package could not be imported. To install use:")
    print("> pip install panoptes-client")
    print("Or activate your panoptes-client enabled anaconda environment")
    quit()


def main():
    actions = (
        ('upload', 'load images to zooniverse'),
        ('get_export', 'Get annotation and other exports')
    )
    p = ActionDispatcher(actions)
    p.dispatch(globals())


def upload(args):
    """
    %prog upload img_directory zoo_project_id --subject subject_setID
    """
    p = OptionParser(upload.__doc__, usage="Upload images from img_directory to zooniverse project with zoo_project_id.")
    p.add_option('--subject', default=False,
        help = 'Designate a subject set id')
    p.add_option('--manifest', default='manifest.csv',
        help = 'Optionally specify a manifest filename')
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())

    img_dir, proj_id = args

    if not os.path.isdir(img_dir):
        print("{} is not a valid path".format(img_dir))
        return

    un, pw, sc = __get_zoo_credentials()

    try:
        Panoptes.connect(username=un, password=pw)
        project = Project.find(id = proj_id)
        if opts.subject:
            subject = SubjectSet.find(opts.subject)
        else:
            subject_set = SubjectSet()
            subject_set.links.project = project
            dispname = input("Enter subject set display name: ")
            subject_set.display_name(dispname)
            subject_set.save()
            project.reload()

        if sc: __save_creds(un, pw)

    except Exception as e:
        tb.print_exc()

    if not os.path.isfile(os.path.join(img_dir, opts.manifest)):
        while True:
            print("There is no manifest, generating...")
                __generate_manifest(img_dir)


def __generate_manifest(img_dir):
    # TODO: get all files that are png or jpg


def export(args):
    """
    %prog get_export project_id

    Get classifications or other export
    """
    p = OptionParser(upload.__doc__)
    p.add_option('-t', '--type', default='classifications'
                help='specify the type of export',
                epilog='Options: []')

    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())

    output_dir = args

    if not os.path.isdir(output_dir):
        print("Output directory is not created")
        quit()

    un, pw, sc = __get_zoo_credentials()

    try:
        Panoptes.connect(username=un, password=pw)
        project = Project.find(id = proj_id)
        print("Getting export, this may take some time.")
        export = project.get_export(opts.type)
        with open(os.path.join(output_dir, \
            dt.now().strftime('zoo_export.%b-%d-%G-%I%:M%p.csv')), \
            'w') as zoof:
            zoof.write(export)

    except:
        tb.print_exc()



def __get_zoo_credentials():
    if os.path.exists("./.zoo_creds.pkl"):
        if input("Used saved login credentials? (y/n)") == 'y':
            with open("./.zoo_creds.pkl", 'rb') as usersfile:
                users = pkl.load(usersfile)
                print(users)
                if not users:
                    return __get_new_creds()
                print("Available users credentials: ")
                print("{:3d} - {}".format(0, 'other'))
                for i, user in enumerate(list(users.keys())):
                    print("{:3d} - {}".format(i+1, user))
                while True:
                    ind = input("Which username? ")
                    if not ind.isdigit(): continue
                    if int(ind) < 0 or int(ind) > len(users.keys()):
                        print("Invalid Entry")
                    elif ind == '0':
                        return __get_new_creds()
                    else:
                        un = list(users.keys())[int(ind)-1]
                        pw = users[un]
                        return un, pw, None

    return __get_new_creds()


def __get_new_creds():

    un = input("Enter zooniverse username: ")
    pw = getpass()

    if input("Would you like to save your credentials if valid? (y/n) ") in ['y', 'Y']:
        sc=True
    else:
        sc=False

    return un, pw, sc


def __save_creds(un, pw):

    print("Saving credentials")
    if os.path.exists(".zoo_creds.pkl"):
        with open(".zoo_creds.pkl", 'rb') as pfile:
            creds = pkl.load(pfile)
            creds[un] = pw
    else:
        creds = {un:pw}

    with open(".zoo_creds.pkl", 'wb') as pfile:
        pkl.dump(creds, pfile)

    return None


if __name__ == '__main__':
    main()
