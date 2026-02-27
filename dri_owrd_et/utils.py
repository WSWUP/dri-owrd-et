import argparse
import datetime
import glob
import logging
import os
import re
import subprocess
import sys
from time import sleep
# Python 3 (or 2 with future module)
import tkinter
import tkinter.filedialog
# Python 2
# import Tkinter
# import tkFileDialog

import ee

ee.Initialize()


def arg_valid_file(file_path):
    """Argparse specific function for testing if file exists

    Convert relative paths to absolute paths
    """
    if os.path.isfile(os.path.abspath(os.path.realpath(file_path))):
        return os.path.abspath(os.path.realpath(file_path))
        # return file_path
    else:
        raise argparse.ArgumentTypeError('{} does not exist'.format(file_path))

            
def get_ini_path(workspace):
    """Open dialog box to allow user to select an .ini file"""
    # Python 3 (or 2 with future module)
    root = tkinter.Tk()
    ini_path = tkinter.filedialog.askopenfilename(
        initialdir=workspace, parent=root, filetypes=[('INI files', '.ini')],
        title='Select the target INI file')
    # Python 2
    # root = Tkinter.Tk()
    # ini_path = tkFileDialog.askopenfilename(
    #     initialdir=workspace, parent=root, filetypes=[('INI files', '.ini')],
    #     title='Select the target INI file')
    root.destroy()
    return ini_path


def unique_keep_order(seq):
    """https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates
       -from-a-list-in-whilst-preserving-order?page=1&tab=active#tab-top
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def parse_int_set(nputstr=""):
    """Return list of numbers given a string of ranges

    http://thoughtsbyclayg.blogspot.com/2008/10/parsing-list-of-numbers-in-python.html
    """
    selection = set()
    invalid = set()

    # Tokens are comma seperated values
    # AttributeError will get raised when nputstr is empty
    try:
        tokens = [x.strip() for x in nputstr.split(',')]
    except AttributeError:
        return set()

    for i in tokens:
        try:
            # typically tokens are plain old integers
            selection.add(int(i))
        except:
            # if not, then it might be a range
            try:
                token = [int(k.strip()) for k in i.split('-')]
                if len(token) > 1:
                    token.sort()
                    # we have items seperated by a dash
                    # try to build a valid range
                    first = token[0]
                    last = token[len(token) - 1]
                    for x in range(first, last + 1):
                        selection.add(x)
            except:
                # not an int and not a range...
                invalid.add(i)
    # Report invalid tokens before returning valid selection
    # print "Invalid set: " + str(invalid)
    return selection
