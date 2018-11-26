# -*- coding: UTF-8 -*-

"""
Upload images to zooniverse project
"""

import importlib
from JamesLab.apps.base import ActionDispatcher, OptionParser

pc = importlib.util.find_spec("panoptes_client")
if pc is None:
    print("panoptes_client package could not be imported. To install use:")
    print("> pip install panoptes-client")
    quit()


def main():
    actions = (
        ('upload', 'load images to zooniverse'),
    )
    p = ActionDispatcher(actions)
    p.dispatch(globals())


def upload(args):
    """
    %prog upload img_directory zoo_project_id --subject subject_setID
    Uploads images from img_directory to zooniverse project with zoo_project_id.
    Can designate a subject set id or create a new one.
    """
    p = OptionParser(upload.__doc__)
    p.add_option('--subject', default=False,
        help = 'Designate a subject set id if subect set already exists.\
                Default is a new subject set will be created.')

    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())

    img_dir, proj_id = args




if __name__ == '__main__':
    main()
