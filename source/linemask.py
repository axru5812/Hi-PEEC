#!/usr/bin/env python
#-*- coding: utf-8 -*-

#------------------------------------------------------------------------------
#Title: Linemask
#Authors:       Matthew Hayes & Axel Runnholm
#Creation date: 2016-07-13
#Description:   This script contains the routines for masking the image edges to
#               prevent spurious detections.

#------------------------------------------------------------------------------


#import packages
#------------------------------------------------------------------------------
# compensation for main diffs between Python 2.7 and 3
from __future__ import division#,print_function

import sys
import scipy as S
import numpy as np
import pyfits as PF
import glob
import os
import subprocess
import shutil
from shutil import copyfile

sys.path.insert(0, './source/')
import filemanagement

#-------------------------------------------------------------------------------



def getlines(fn):
    """Function for getting lines from ds9 reg file
    Input:
        fn (str) - filepath to regfile
    Outputs:
        d (iterable) - iterable with lines from regfile
    """
    fh = open(fn, "r")
    d  = fh.readlines()
    fh.close()
    return d



def get_ends(l):
    x1 = float(l[0])
    y1 = float(l[1])
    x2 = float(l[2])
    y2 = float(l[3])
    if x1 == x2: x1 += 1.  # do not permit x1=x2, otherwise gradient undefined.
    return x1, y1, x2, y2

def get_nearedge(x1,y1,x2,y2, Nx, Ny):
    cx = (x1+x2)/2.
    cy = (y1+y2)/2.
    edge_arr = S.array([ cx, Nx-cx, cy, Ny-cy ])    # distance to [ left, right, bottom,  top ]
    if   edge_arr.argmin() == 0: return "left"
    elif edge_arr.argmin() == 1: return "right"
    elif edge_arr.argmin() == 2: return "bottom"
    elif edge_arr.argmin() == 3: return "top"
    else :
        print "something screwy finding the nearest edge!"
        sys.exit(1)

def get_fn(x1,y1,x2,y2):
    m = (y2-y1)/(x2-x1)
    c = y1 - m*x1              # c = y - mx
    return m,c

def create_mask(ref, lines):
    """Function for creating a boolean mask
    Inputs:
        ref (str) - path to reference image
        lines (str) - path to region file
    Outputs:
        mask (np.array) - matrix with 1 if we are inside the selected region and 0 if we are outside.
    """
    # Main function
    fnRef   = ref
    fnLines = lines

    dat  = [ l.replace("line(", "").split(")")[0].split(",")  for l in getlines(fnLines) if l.startswith("line") ]

    head   = PF.getheader(fnRef)
    img    = PF.getdata(fnRef)
    mask   = S.ones_like(img)
    Ny, Nx = img.shape

    dx  = S.zeros_like(mask)
    dy  = S.zeros_like(mask)
    for i in range(Nx): dx[:,i] = i+1
    for i in range(Ny): dy[i]   = i+1

    for d in dat :
        x1, y1, x2, y2 = get_ends(d)
        #print x1, y1, "  ->  ", x2, y2
        edge_near = get_nearedge(x1, y1, x2, y2, Nx, Ny)
        m, c = get_fn(x1, y1, x2, y2)
        #print "grad=", m, "    intercept=",c

        ineq = None
        if   edge_near == "top"    : ineq = "gt"
        elif edge_near == "bottom" : ineq = "lt"
        elif edge_near == "left":
            if   m>0: ineq = ineq = "gt"
            else    : eneq = ineq = "lt"
        elif edge_near == "right":
            if   m>0: ineq = ineq = "lt"
            else    : eneq = ineq = "gt"

        if ineq == "gt": ind = dy > (m*dx + c)
        else           : ind = dy < (m*dx + c)
        mask[ind]  = 0.

    PF.writeto('mask.fits', mask, header=head, clobber=True)

    return mask

def remove_edgedetections(catalog, ref, lines):
    """Function for removing clusters from the catalog if they are not inside the region specified.
    Inputs:
        ref (str) - path to reference image
        lines (str) - path to region file
    Outputs:
        none
    Effects:
        removes detections outside defined region from cluster catalog
    """

    mask = create_mask(ref, lines)

    xx, yy, fwhm, class_s, mag = np.loadtxt(catalog, skiprows=5, unpack=True)

    with open(catalog,'r') as f:
        lines = f.readlines()
    i=0
    with open(catalog,'w') as f:
        for line in lines:
            if line.startswith('#') == True:
                f.write(line)
            else:
                x = xx[i]
                y = yy[i]
                if mask[y,x] == 1:
                    l = '{}\t{}\t{}\t{}\t{}\n'.format(x, y, fwhm[i], class_s[i], mag[i] )
                    f.write(l)
                i+=1

def mask_edges(userinput,extraction_cat):
    ref_image =userinput['DATA'] + '/' + userinput['IMAGE']
    regfilename = userinput['OUTDIR'] + '/init/*.reg'

    if not glob.glob(regfilename):
        print 'There is no .regfile in the init directory'
        inp = raw_input('Do you wish to create one? (y/n) ')
        if inp == 'y':
            os.chdir(userinput['PYDIR'] + '/init')
            cmd = 'ds9 ' + ref_image + ' -scale log -scale limits -0.1 100 -regions shape line'
            process  = subprocess.Popen(cmd, shell=True)
            process.wait()
            print 'Checking for saved image'
            os.chdir(userinput['OUTDIR'])
            if not glob.glob(userinput['PYDIR'] + '/init/*.reg'):
                filemanagement.shutdown('Still no .reg file detected. Shutting down', userinput)
            else:
                print 'Removing sources outside mask.'
                file = glob.glob(userinput['PYDIR'] + '/init/*.reg')[0].split('/')[-1]
                shutil.copyfile(userinput['PYDIR'] + '/init/' + file,userinput['OUTDIR'] + '/init/' + file)
                regfile = glob.glob(regfilename)[0]
        elif inp =='n':
            print 'Skipping edge removal step'
            return 0
        else:
            print 'Not a recognised input. Skipping edge-removal'
            return 0
    else:
        regfile = glob.glob(regfilename)[0]

    try:
        remove_edgedetections(extraction_cat, ref_image, regfile)
        return 1
    except:
        print 'Edge masking failed. Proceeding without it. Make sure to save the .reg file in image coordinates.'
        return 0