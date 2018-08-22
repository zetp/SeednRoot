#!/usr/bin/env python2.7

# TO DO:
# Consider moving more code to numpy
#I = numpy.asarray(Image.open('test.jpg'))
#im = Image.fromarray(numpy.uint8(I))
# idea: multi thread to detect background and marker pixels at the same time

from os import remove, path, listdir
from sys import stdout, argv
import datetime
import numpy as np

from PIL import Image
from scipy import ndimage, misc

display_help = 0
user_input = 0

#### /// PARAMETERS TO CHANGE IF NEEDED ///
# marker parameters
PB2 = 45   #p2# percent Blue max value 
PB1 = 15   #p1# percent Blue min value
BR = 200   #b# maximum brightness (r+g+b)/3 
MC = 10000   #m# cutoff value for marker pixel clusters to be erased (to get rid of selected seeds)
DL = 5     #d# how many times make binary dilation for marker mask
# Bacground parameters
FC = 1000  #f# cutoff value for bacground holes to be erased (to get rid of selected seeds)
ER = 8     #e# how many times make binary erosion for selected fields
# Other parameters
image_x = 0#x# do not save inspection pictures
Pow_min = 1000000
Pow_min1 = 100000
#### \\\ PARAMETERS TO CHANGE IF NEEDED \\\

user_inputs = [] # to bedzie lista plikow wejsciowych
lista_nazw = [] # to bedzie lista nazw dla sekcji

### command line arguments
if (len(argv) > 1):
    argv.pop(0) # usuac pierwsza rzecz z listy jaka jest sciezka do siebie
    for arg in argv: #przez wszystkie argumenty przejsc
        if "-p2=" in arg:
            arg = arg.replace("-p2=", "")
            try:
                p2 = int(arg)
                PB2 = p2
            except: continue

        elif "-p1=" in arg:
            arg = arg.replace("-p1=", "")
            try:
                p1 = int(arg)
                PB1 = p1
            except: continue
            
        elif "-b=" in arg:
            arg = arg.replace("-b=", "")
            try:
                b = int(arg)
                BR = b
            except: continue
            
        elif "-m=" in arg:
            arg = arg.replace("-m=", "")
            try:
                m = int(arg)
                MC = m
            except: continue
            
        elif "-d=" in arg:
            arg = arg.replace("-d=", "")
            try:
                d = int(arg)
                DL = d
            except: continue
            
        elif "-f=" in arg:
            arg = arg.replace("-f=", "")
            try:
                f = int(arg)
                FC = f
            except: continue
            
        elif "-e=" in arg:
            arg = arg.replace("-e=", "")
            try:
                e = int(arg)
                ER = e
            except: continue
            
        elif "-N=" in arg:
            arg = arg.replace("-N=", "")
            try:
                e = str(arg)
                lista_nazw = e.split(",")
            except: continue

        elif "-x" in arg:
            image_x = 1

        elif ("-h" in arg or "-help" in arg or "--h" in arg or "--help" in arg) is True:
            display_help = 1
            
        elif path.isfile(arg) is True: # identifying passed file
            try:
                im = Image.open(arg) # is that an image?
                user_inputs.append(arg) # dodac do listy
            except: continue
            
        elif path.isdir(arg) is True: # identifying passed folder
            for f in listdir(arg):
                if not "_section" in f:    # skip _out files (if processing same folder more tha once)
                    f = path.join(arg, f)
                    try:
                        im = Image.open(f) # is that an image?
                        user_inputs.append(f) # dodac do listy
                    except: continue

### command line arguments

print "This program will try to identify sections on plate(s)"
print "Zbyszek Pietras 2013"
print "Use -h flag to show help"
print ""

### HELP
if display_help == 1:
    print "Use of command line argments:\n\
 /path/to/image\n\
 -x save diagnostic images\n\
 -h show this help\n\n\
 Names for sections:\n\
 -N=[names] names have to be divided by comma WITHOUT space\n\
 example: name1,name2,name3,name4\n\n\
 Plate section detection variables:\n\
 -f=[integer] No. of pixels cuoff value for background holes (default value: %d)\n\
 -e=[integer] how many times make binary erosion for selected fields (default value: %d)\n\n\
 Marker detection variables:\n\
 -p1=[integer] %% Blue max value (default value: %d)\n\
 -p1=[integer] %% Blue min value (default value: %d)\n\
 -b=[integer] maximum brightness (default value: %d)\n\
 -m=[integer] cutoff value for marker pixel clusters (default value: %d)\n\
 -d=[integer] how many times make binary dilation for marker mask (default value: %d)" % (FC, ER, PB1, PB2, BR, MC, DL)
    exit()
### /HELP

if user_inputs == []:
    user_input = raw_input('Path to image please:\n')
    
    ### does file exist?
    is_file = path.isfile(user_input)
    if is_file is False:
        print "ERROR: file does not exist.", exit()
     
    ### is file an image?
    try:
        im = Image.open(user_input)
        # is image = OK
    except:
        print "ERROR: Cannot open file.", exit()  
        
    user_inputs = [user_input]

### ///Subroutines///

# COLOUR FILTER SUB
def colour_check(col):
    """goes pixel by pixel copying only ones that fit the criteria"""
    counter = 0
    percent = 1
    
    if col is "field": norm_name = "identifying background pixels: "; col_name = "field.png"
    elif col is "marker":  norm_name = "identifying marker pixels: "; col_name = "marker.png"
    
    stdout.write("\r"+norm_name+"opening image"); stdout.flush()
    n = Image.open(user_input)
    if n.mode == "RGBA":
        ### THIS CHANGES TRANSPARENT PIXELS TO BLACK PIXELS
        stdout.write("\r"+norm_name+"removing transparency"); stdout.flush()
        datas = n.getdata()
        newData = list()
        for item in datas:
            if item[0] == 255:
                newData.append((0, 0, 0, 0))
            else:
                newData.append(item)
        n.putdata(newData)
    stdout.write("\r"+norm_name+"converting           "); stdout.flush()
    n = n.convert(mode="RGB")
    m = n.load()
    s = n.size
    # iterate through x and y (every pixel) 
    stdout.write("\r"+norm_name+"               "); stdout.flush()
    for x in xrange(s[0]):
        for y in xrange(s[1]):
            r, g, b = m[x, y]
# counter code - can be erased (slows down code excecution on small images)
            counter = (counter + 1)
            if counter == one_p:

                stdout.write("\r"+norm_name+"%2d%% " % percent) # add "+ c" to parenthesis
                stdout.flush()
                percent = (percent + 1)
                counter = 0
# /counter code - can be erased
            if col is "field":
                if (b > g > r):   # or (b > g and b > r) slightly different results
                    m[x, y] = (0, 0, 0)
                else: m[x, y] = (255, 255, 255)  # everything else goes white
                
            elif col is "marker":
                if ((PB2 > ((b*100)/(r+g+b+0.0001)) > PB1) and ((r+g+b)/3) < BR):
                    m[x, y] = (255, 255, 255)
                else: m[x, y] = (0, 0, 0) # everything else goes black
                
    n2 = n.convert(mode="L")            
    if image_x == 1:        
        name_col = "_".join([filename, col_name]) 
        n2.save(name_col, "PNG") # save the doctored image
    
    im = Image.fromarray(np.uint8(n2))
    return im
    
# COUNTING SUB

def deling_with_marker(obrazek):

    name_col = "_".join([filename, "marker.png"])
    col_name = "_".join([filename, "markerF.png"])
    stdout.write(str("\rreading image...")); stdout.flush()
    
    #n4 = Image.open(name_col)
    #n4 = n4.convert(mode="L") # open in B&W for fast processing
    #m = np.asarray(n4)
    m = np.asarray(obrazek)
    
### get rid of small groups of pixels (seeds)    
    stdout.write("\rsniffing marker..."); stdout.flush()
    # get rid of detected parts of seed
    bs = ndimage.morphology.generate_binary_structure(2,2)
    labeled, nr_objects = ndimage.measurements.label(m, structure=bs)
    sizes = (ndimage.sum(m, labeled, range(nr_objects + 1)))/255
    mask_size = sizes < MC
    remove_pixel = mask_size[labeled]
    labeled[remove_pixel] = 0
    non_zeros = labeled > 0
    labeled[non_zeros] = 1
    m = labeled
    for x in range(0, DL):
        m = ndimage.binary_dilation(m).astype(m.dtype) # expand
        
    if image_x == 1:
       misc.imsave(col_name, m)
            
    m = m.astype(bool) # change array type to bool (true/false)
    
    return m

def counting_fields(obrazek):
    """this is for counting the objects in the image na more"""
    name_col = "_".join([filename, "field.png"])
    col_name1 = "_".join([filename, "fieldF.png"])
    stdout.write("\rreading image...  "); stdout.flush()
    
    m = np.asarray(obrazek)

### get rid of small groups of pixels (seeds)
    stdout.write("\rdetecting sections: celaning positive..."); stdout.flush()
    bs = ndimage.morphology.generate_binary_structure(2,2) # when used this joins diagonal pixels into one label
    labeled, nr_objects = ndimage.measurements.label(m, structure=bs)
    
    sizes = (ndimage.sum(m, labeled, range(nr_objects + 1)))/255 # object white so divided by 255 = No fo pixels
    mask_size = sizes < FC
    remove_pixel = mask_size[labeled]
    labeled[remove_pixel] = 0 # makes all small artefacts black
    non_zeros = labeled > 0
    labeled[non_zeros] = 255 # unify all labels to be white
    m = labeled
    
### Inverting image:
    stdout.write("\rdetecting sections: inverting image...  "); stdout.flush()
    m[m < 1] = 50 # < 1 is 0 values set temporary to 50
    m[m > 51] = 0 # > 1 are 255 values set to 0
    m[m > 1] = 255 # now > 1 are only 50 and set to 255
    
### get rid of small groups of pixels (seeds)
    stdout.write("\rdetecting sections: celaning negative..."); stdout.flush()
    labeled, nr_objects = ndimage.measurements.label(m, structure=bs)
    
    sizes = (ndimage.sum(m, labeled, range(nr_objects + 1)))/255 # object white so divided by 255 = No fo pixels
    mask_size = sizes < FC
    remove_pixel = mask_size[labeled]
    labeled[remove_pixel] = 0 # makes all small artefacts black
    non_zeros = labeled > 0
    labeled[non_zeros] = 255 # unify all labels to be white
    m = labeled
    mass_centre = ndimage.measurements.center_of_mass(m)
     
    labeled, nr_objects = ndimage.measurements.label(m, structure=bs)
    
    ### THIS PART IS TO ORDER FIELDS CLOCKWISE
    list_labels = range(nr_objects)
    list_labels.append(nr_objects)
    list_labels.pop(0)
    mass_centres = (ndimage.measurements.center_of_mass(m, labeled, list_labels))
    
    _i = iter(list_labels)
    _j = iter(mass_centres)
    slownik_1 = dict(zip(_j, _i))
    
    sorted_1 = sorted(slownik_1.iteritems()) # ascending 
    sorted_2 = sorted(slownik_1.iteritems(), reverse=True) # descending
    
    sorted_filed_labels = []
    
    for k in sorted_1:
        if (k[0])[1] > mass_centre[1]:
            _key = slownik_1[k[0]]
            sorted_filed_labels.append(_key)
            
    for k in sorted_2:
        if (k[0])[1] < mass_centre[1]:
            _key = slownik_1[k[0]]
            sorted_filed_labels.append(_key)
                
    ### ///THIS PART IS TO ORDER FIELDS CLOCKWISE
    
    if image_x == 1:
       misc.imsave(col_name1, m)
    
    stdout.flush(); print "\rdetecting sections: %d sections found    " % nr_objects
    
### Mask and save each section
    #OPEN ORIGINAL IMAGE
    n = misc.imread(user_input)
    
    Ktory_obiekt = 0
    Ktory_obiekt2 = 0
    while nr_objects > 0:
        nr_objects = nr_objects - 1
        
        if len(sorted_filed_labels) == 0:
            Ktory_label = 1
        else:
            Ktory_label = sorted_filed_labels[Ktory_obiekt]
        
        Ktory_obiekt = Ktory_obiekt + 1
        stdout.write("\rextracting section %d:" % Ktory_obiekt); stdout.flush()
        labeled_single = labeled.copy() # have to copy array to avoid changing the original
        
        # This is to extract just this field
        stdout.write("\rextracting section %d: juggling" % Ktory_obiekt); stdout.flush()
        labeled_single[labeled_single < Ktory_label] = 0 # wszystko inne bo mniejsze i wieksze ale nie takie samo jak
        labeled_single[labeled_single > Ktory_label] = 0
        labeled_single[labeled_single > 0] = 1
        if np.sum(labeled_single) > Pow_min1:
        
            # shrink the field
            stdout.write("\rextracting section %d: nibbling" % Ktory_obiekt); stdout.flush()
            for x in range(0, ER):
                labeled_single = ndimage.binary_erosion(labeled_single).astype(labeled_single.dtype)
        
            # Now invert array and chnage it to type bool (true, false)
            stdout.write("\rextracting section %d: defying logic" % Ktory_obiekt); stdout.flush()
            labeled_single = np.logical_not(labeled_single)
        
            # now lets make the mask black
            stdout.write("\rextracting section %d: cheating     " % Ktory_obiekt); stdout.flush()
            n_copy = n.copy() # copy opened original picture
            stdout.write("\rextracting section %d: painting it black" % Ktory_obiekt); stdout.flush()
            n_copy[labeled_single] = 0 # try to make object black
            n_copy[marker_mask] = 0 # make all marker black
        
            stdout.write("\rextracting section %d: running with scissors" % Ktory_obiekt); stdout.flush()
            n_copy = Image.fromarray(np.uint8(n_copy)) 
            bbox = n_copy.getbbox() # this should find nonblack pixels
        
            Pow_S = 0
        
            try:
                Pow_S = abs(bbox[2] - bbox[0]) * abs(bbox[3] - bbox[1])
            except: stdout.flush();print"\rextracting section %d: section too small    " % Ktory_obiekt;continue
        
            if Pow_S > Pow_min:
            
                if len(lista_nazw) == 0:
                    nazwa_wlasna = Ktory_obiekt2 + 1
                elif Ktory_obiekt2 >= len(lista_nazw):
                    nazwa_wlasna = Ktory_obiekt2 + 1
                else:
                    nazwa_wlasna = lista_nazw[Ktory_obiekt2]
            
                Ktory_obiekt2 = Ktory_obiekt2 + 1
        
                n_copy = n_copy.crop(bbox)
        
                if len(lista_nazw) == 0:
                    col_name = "_".join([filename, ("section%d.png" % nazwa_wlasna)])
                else:
                    col_name = "_".join([filename, ("%s.png" % nazwa_wlasna)])
        
                misc.imsave(col_name, n_copy)
        
                stdout.flush(); print "\rextracting section %d: done                 " % Ktory_obiekt
        else: stdout.flush(); print"\rextracting section %d: section too small    " % Ktory_obiekt
      
### ///Subroutines///

now = datetime.datetime.now()
first_item = user_inputs[0]
directory = path.dirname(first_item) # directory for the first file of user input

####
# dla kazdej rzeczy z listy plikow
####
for user_input in user_inputs:

 ### extract file name and path
 base = path.basename(user_input)
 real_filename = path.splitext(base)[0]
 filename = path.splitext(user_input)[0] # this gives full path to file with file name but w/o extension
 im = Image.open(user_input)
 im_width, im_height = im.size # get image dimetions in pixels
 one_p = ((im_width*im_height)/100) # Calculate 1% value of No of pixels

 ### Start LOG
 print "Analysing file:", user_input

 ### COLOUR CHECK
 obrazek1 = colour_check("field")
 stdout.flush(); print "\ridentifying background pixels: done  "
 obrazek2 = colour_check("marker")
 stdout.flush(); print "\ridentifying marker pixels: done  "

 #### LICZENIE
 marker_mask = deling_with_marker(obrazek2)
 counting_fields(obrazek1)
# print "\nField: %s seed No.: %d " % (real_filename,No_red)


 ### CLOSING
 after = datetime.datetime.now()
 run_time = (after - now)
 print "Run time: ", str(run_time)