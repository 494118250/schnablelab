'''
JamesLab CLI tool
Calls Zookeeper class
'''

from JamesLab.apps.base import ActionDispatcher, OptionParser
import sys

def main():
    actions = (
        ('upload', 'load images to zooniverse'),
        ('export', 'Get annotation and other exports'),
        ('manifest', 'Generate a manifest for zooniverse subject set upload')
    )
    p = ActionDispatcher(actions)
    p.dispatch(globals())


def upload(args):
    '''
    %prog upload imgdir projid

    - imgdir: Path to directory of the images to be uploaded
    - projid: Zooniverse project id (4 - 5 digit number)

    DESC:
        Uploads images from the image directory to zooniverse
        project. If there is no manifest will generate one.
    '''

    from JamesLab.Zootils import upload as load

    p = OptionParser(upload.__doc__)
    p.add_option('-s', '--subject', default=False,
                 help='Designate a subject set id.')
    p.add_option('-q', '--quiet', default=False,
                 help='Silences output when uploading images to zooniverse.')
    p.add_option('-w', '--workflow', default=None,
                 help='Designate a workflow id to link this subject set.')
    p.add_option('-c', '--convert', default=False,
                 help="Compress and convert files to jpg for faster load times"
                 + " on zooniverse.\n"
                 + " Command: magick -strip -interlace Plane -quality 85%"
                 + " -format jpg <img_directory>/<filename>.png")

    opts, args = p.parse_args(args)

    if len(args) != 2:
        p.print_help()
        exit(False)

    imgdir, projid = args

    load(imgdir, projid, opts)

    return True


def export(args):
    '''
    %prog export proj_id outfile

    - proj_id: The project id of the zooniverse project

    DESC: Fetches an export from the specified zooniverse project id.
    '''

    from JamesLab.Zootils import export as exp

    p = OptionParser(export.__doc__)
    p.add_option('-t', '--type', default='classifications',
                 help='Specify the type of export')

    opts, args = p.parse_args(args)

    if len(args) != 2:
        exit(not p.print_help())

    projid, outfile = args

    exp(projid, outfile, opts)

    return True


def manifest(args):
    '''
    %prog manifest image_dir

    - img_dir: The image directory in which to generate the manifest.

    DESC: Generates a manifest inside the specified image directory.
    '''
    from JamesLab.Zootils import manifest as mani

    p = OptionParser(manifest.__doc__)
    opts, args = p.parse_args(args)

    if len(sys.argv) != 1:
        exit(not p.print_help())

    imgdir = args[1]

    mani(imgdir)

    return True


if __name__ == '__main__':
    main()
