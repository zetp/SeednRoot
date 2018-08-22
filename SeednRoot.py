#!/usr/bin/env python2.7

### TO DO: CALIBRATION: iterations of 2-3 values with known No of roots (if No_roots higher then, lower then)
### MEASUREMENT of colour saturation [max(r,g,b)-min(r,g,b)]/(r+g+b)  (grey <0.10 or 0.15, colour ~0.2 and above)
  
from os import remove, path, listdir
from sys import stdout, argv
import datetime
import numpy as np

from PIL import Image
from scipy import ndimage, misc

display_help = 0
user_input = 0

#### /// PARAMETERS TO CHANGE IF NEEDED ///
# ROOT PARAMETERS
Z_factor = 1.5 # (r + g) / b
prcnt_B = 27 # % niebieskiego
bright = 130 # srednia jasnosc 140 dla duzych korzeni 130
root_cutoff_size = 10 # wielkosc korzenia 5 dla duzych korzeni 15

# SEED PARAMETERS
color_cutoff = 50 # ile razem moze byc poza glownym kolorem (w liczeniu nasion)
filter_do = 1 # 1 - use gaussian filter, 0 - dont use gaussian filter
filter_val = 2.5 # filter value (gaussian filter to blur the image) bigger is better for dots
Z_cutoff = 3.0 # cutoff do nasion

image_x = 1 # save B&W images for later inspection

#### /// PARAMETERS TO CHANGE IF NEEDED ///

user_inputs = [] # to bedzie lista plikow wejsciowych

### command line arguments
if (len(argv) > 1):
    argv.pop(0) # usuac pierwsza rzecz z listy jaka jest sciezka do siebie
    for arg in argv: #przez wszystkie argumenty przejsc
        if "-c=" in arg:
            arg = arg.replace("-c=", "")
            try:
                c = int(arg)
                color_cutoff = c
            except: continue
            
        elif "-z=" in arg:
            arg = arg.replace("-z=", "")
            try:
                z = float(arg)
                Z_factor = z
            except: continue
            
        elif "-p=" in arg:
            arg = arg.replace("-p=", "")
            try:
                p = int(arg)
                prcnt_B = p
            except: continue
            
        elif "-b=" in arg:
            arg = arg.replace("-b=", "")
            try:
                b = int(arg)
                bright = b
            except: continue
            
        elif "-s=" in arg:
            arg = arg.replace("-s=", "")
            try:
                s = int(arg)
                root_cutoff_size = s
            except: continue
            
        elif "-y=" in arg:
            arg = arg.replace("-y=", "")
            try:
                y = float(arg)
                Z_cutoff = y
            except: continue
                     
        elif "-v=" in arg:
            arg = arg.replace("-v=", "")
            try:
                v = float(arg)
                filter_val = v
            except: continue
            
        elif "-f" in arg:
            filter_do = 0
        elif "-x" in arg:
            image_x = 0

        elif ("-h" in arg or "-help" in arg or "--h" in arg or "--help" in arg) is True:
            display_help = 1
   
        elif path.isfile(arg) is True: # identifying passed file
            try:
                im = Image.open(arg) # is that an image?
                user_inputs.append(arg) # dodac do listy
            except: continue

        elif path.isdir(arg) is True: # identifying passed folder
            for f in listdir(arg):
                if not "_out.png" in f:    # skip _out files (if processing same folder more tha once)
                    f = path.join(arg, f)
                    try:
                        im = Image.open(f) # is that an image?
                        user_inputs.append(f) # dodac do listy
                    except: continue

### command line arguments

print ""
print "This program will try to count seeds, roots and then calculate % of germinated seeds.\n\
Use -h flag to show help."
print "Zbyszek Pietras 2012"
print ""

### HELP
if display_help == 1:
    print "Use of command line argments:\n\
 /path/to/image(s) or folder\n\
 -x do not save composite images\n\
 -h show this help\n\n\
 Seed detection variables:\n\
 -f skip gaussian filter\n\
 -v=[integer or float] gaussian filter value (default value: %.1f)\n\
 -c=[integer] blue colour cutoff (default value: %d)\n\
 -y=[float] (r+g)/b factor cutoff value (default value: %.1f)\n\n\
 Root detection variables:\n\
 -z=[float] (r+g)/b factor cutoff value (default value: %.1f)\n\
 -p=[integer] %% of blue cutoff value (default value: %d)\n\
 -b=[integer] brithness cutoff value (default value: %d)\n\
 -s=[integer] minimum size of root (in pixels, default value: %d)" % (filter_val, color_cutoff, Z_cutoff, Z_factor, prcnt_B, bright, root_cutoff_size)
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
# LOG WRITE SUB
def write_to_log(txt):
    """this writes txt to log file + closes the file"""
    text_log = open(log_name, "a")
    text_log.write(txt)
    text_log.close()
    
    
###    the function below was taken from the stackoverflow:
###    https://stackoverflow.com/questions/3684484/peak-detection-in-a-2d-arrays
def detect_peaks(image):
    """
    Takes an image and detect the peaks using the local maximum filter.
    Returns a boolean mask of the peaks (i.e. 1 when
    the pixel's value is the neighborhood maximum, 0 otherwise)
    """

    # define an 8-connected neighborhood
    neighborhood = ndimage.morphology.generate_binary_structure(2,1)

    #apply the local maximum filter; all pixel of maximal value 
    #in their neighborhood are set to 1
    local_max = (ndimage.filters.maximum_filter(image, footprint=neighborhood)==image) 
    #local_max is a mask that contains the peaks we are 
    #looking for, but also the background.
    #In order to isolate the peaks we must remove the background from the mask.

    #we create the mask of the background
    background = (image==0)

    #a little technicality: we must erode the background in order to 
    #successfully subtract it form local_max, otherwise a line will 
    #appear along the background border (artifact of the local maximum filter)
    eroded_background = ndimage.morphology.binary_erosion(background, structure=neighborhood, border_value=1)

    #we obtain the final mask, containing only peaks, 
    #by removing the background from the local_max mask
    detected_peaks = local_max - eroded_background

    return detected_peaks
    #return np.where(detected_minima)  location of the peaks

# COLOUR FILTER SUB
def colour_check(col):
    """goes pixel by pixel copying only ones that fit the criteria"""
    counter = 0
    percent = 1
    
    if col is "seed": norm_name = "Looking at seeds:  "; col_name = "seed.png"
    elif col is "root": norm_name = "Looking at roots:  "; col_name = "root.png"
#    spin_no = 0
#    cursor="/-\|"
    stdout.write("\r"+norm_name+"opening image"); stdout.flush()
    n = Image.open(user_input)
    if n.mode == "RGBA":
        ### THIS CHANGES TRANSPARENT PIXELS TO BLACK PIXELS
        stdout.write("\r"+norm_name+"removing transparency"); stdout.flush()
        datas = n.getdata()
        newData = list()
        for item in datas:
            if item[3] == 0:
                newData.append((0, 0, 0, 255))
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
# counter code - can be erased (slows down code on small images)
            counter = (counter + 1)
            if counter == one_p:
#                spin_no = spin_no + 1
#                if spin_no == 4:
#                    spin_no = 0
#                c = cursor[spin_no]
                stdout.write("\r"+norm_name+"%2d%% " % percent) # add "+ c" to parenthesis
                stdout.flush()
                percent = (percent + 1)
                if percent > 99:
                    percent = 100
                counter = 0
# /counter code - can be erased

            if col is "seed":
                if ((r > g > b) and (((float(g)+float(r))/(float(b)+0.00001)) > Z_cutoff) and (b > color_cutoff)):
                    m[x, y] = (255, 255, 255)
                else: m[x, y] = (0, 0, 0)  # everything else goes black

            elif col is "root":
                if  (((float(g)+float(r))/(float(b)+0.00001)) > Z_factor) and (((float(b * 100)/float(b + r + g)) > prcnt_B) and ((float(b + r + g)/3.0) > bright)):
                    m[x, y] = (255, 255, 255)
                elif (((float(g) + float(r)) / (float(b)+0.00001)) > Z_factor):
                    m[x, y] = (250, 250, 250)
                else: m[x, y] = (0, 0, 0)  # everything else goes black

    name_col = "_".join([filename, col_name]) 
    n = n.convert(mode="L")
    n.save(name_col, "PNG") # save the doctored image
    
# COUNTING SUB

def counting_dots(col):
    """this is for counting the objects in the image"""
    if col is "seed":
        col_name2 = "seed.png"; norm_name = "seed"; name_col = "_".join([filename, "seed.png"])
        stdout.write(str("\rReading "+norm_name+" image")); stdout.flush()
        n = Image.open(name_col)
    elif col is "root":
        col_name2 = "root2.png"; norm_name = "root"; name_col = "_".join([filename, "root.png"])
        stdout.write(str("\rReading "+norm_name+" image")); stdout.flush()
        n = Image.open(name_col)
    
    if col is "root":
### THIS SET ALL PIXELS THAT ARE GREY TO BLACK
        datas = n.getdata()
        newData = list()
        for item in datas:
            if item == 250:
                newData.append(0)
            else:
                newData.append(item)
        n.putdata(newData)
    
        m = np.asarray(n)
        
        
        stdout.write(str("\rRoot detection... ")); stdout.flush()
        
        bs = ndimage.morphology.generate_binary_structure(2,2) # when used this joins diagonal pixels into one label
        labeled, nr_objects = ndimage.measurements.label(m, structure=bs)
    
        sizes = (ndimage.sum(m, labeled, range(nr_objects + 1)))/255 # all pixels are white (val=255) so this gives No of pixels
        mask_size = sizes < root_cutoff_size # cutoff size
        remove_pixel = mask_size[labeled]
        labeled[remove_pixel] = 0 # makes all small artefacts black
        non_zeros = labeled > 0
        labeled[non_zeros] = 255 # unify all labels to be white
        m = labeled
        labeled, nr_objects = ndimage.measurements.label(m, structure=bs)
        
        if image_x == 0:
          remove(name_col)
       
    
    if col is "seed":

        n = n.convert(mode="L") # open in B&W for fast processing
        m = np.asarray(n)
        
        if filter_do is 1:
            stdout.write(str("\rGaussian on image")); stdout.flush()
            m = ndimage.gaussian_filter(m, filter_val)

        remove(name_col)
    
        stdout.write(str("\rSeed detection... ")); stdout.flush()
        peaks = detect_peaks(m)
        peaks = ndimage.binary_dilation(peaks).astype(peaks.dtype) # to join pixels that belong to one max
        bs = ndimage.morphology.generate_binary_structure(2,2)
        labeled, nr_objects = ndimage.measurements.label(peaks, structure=bs)
        
    if image_x == 1:
       if col is "root":
          name_col = "_".join([filename, col_name2]) 
          peaks_img = m.astype(np.int)*255
          misc.imsave(name_col, peaks_img)
          
       elif col is "seed":
          name_col = "_".join([filename, col_name2])
          peaks_img = peaks.astype(np.int)*255
          misc.imsave(name_col, peaks)

    return nr_objects
    
### ///Subroutines///
now = datetime.datetime.now()
first_item = user_inputs[0]
directory = path.dirname(first_item) # directory for the first file of user input
log_name = "".join([directory, "/", (now.strftime("%Y%m%dT%H%M%S")), "_log.txt"]) #name of log

write_to_log(str(now)) # create log
if filter_do == 1:
    f_str = "ON"
elif filter_do == 0:
    f_str = "OFF"
write_to_log("\nParameters for seed detection: Gaussian filter - %s, Filter val - %.1f, Blue cutoff - %d, Z cutoff - %.1f" % (f_str, filter_val, color_cutoff, Z_cutoff))
write_to_log("\nParameters for root detection: Z cutoff - %.1f, Blue cutoff - %d%%, Brithness - %d, Minimum root size  - %d pixels\n" % (Z_factor, prcnt_B, bright, root_cutoff_size))

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
 colour_check("seed")
 stdout.flush(); print "\rLooking at seeds: done  "
 
 colour_check("root")
 stdout.flush(); print "\rLooking at roots: done  "

 #### LICZENIE
 No_seeds = counting_dots("seed")
 stdout.flush(); print "\rField: %s seed No.: %d " % (real_filename,No_seeds)
 write_to_log("\nField: %s seed No.: %d " % (real_filename,No_seeds))
 No_roots = counting_dots("root")
 stdout.flush(); print "\rField: %s root No.: %d " % (real_filename,No_roots)
 write_to_log(" root No.: %d " % No_roots)
 
 if No_seeds == 0:
    print "WARNING: No seeds detected!"
    write_to_log("WARNING: No seeds detected!")
 else:
    x = (float(No_roots)*100)/float(No_seeds)
    print "Germinated seeds: %.1f%%" % (x)
    write_to_log(" germinated: %.1f %%" % x)
 
 if image_x == 1:
    print "Writing nice image for you..."; stdout.flush()
    name_placki = "_".join([filename, "root.png"])
    name_seed = "_".join([filename, "seed.png"])
    name_root = "_".join([filename, "root2.png"])
    out_name = "_".join([filename, "out.png"])
    
    background = Image.open(name_placki)
    overlay = Image.open(name_seed)
    background = background.convert("RGBA")
    overlay = overlay.convert("RGBA")
    new_img = Image.blend(background, overlay, 0.5)
    background = new_img
    overlay = Image.open(name_root)
    overlay = overlay.convert("RGBA")
    new_img = Image.blend(background, overlay, 0.5)
    new_img = new_img.convert(mode="L")
    new_img.save(out_name,"PNG")
    print "Deleting temporary files...  "; stdout.flush(); 
    remove(name_placki)
    remove(name_seed)
    remove(name_root)

### CLOSING
after = datetime.datetime.now()
run_time = (after - now)
print "Run time: ", str(run_time)