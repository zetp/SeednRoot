# SeednRoot
Image processing in python. These two scripts automate counting of germinated and non-germinated Arabidopsis seeds using pictures as input. This in general automates investigation of [seed dormancy](https://en.wikipedia.org/wiki/Seed_dormancy) phenomena.

First script PlateSplitter.py  will divide the picture of plate into fields and order them clockwise. 
```
PlateSplitter.py test_image.jpg
```
you can also provide names (using -N= flag) for fields, which comes handy in further analysis. For more info run:
```
PlateSplitter.py -h
```

The SeednRoot script will count germinated and not-germinated seeds and write out the log file with the results, time and date of analysis and values of parameters used.
Additionally it will also greysale images that one can inspect for accuracy and calibration purposes - the potential seeds are marked as dark grey areas, the smaller light grey dots mark centre of the seed and these are counted as seed in final result. Finally the roots are displayed as white areas and each area is counted as root.
Script will process individual images but it is most frequently used on folders 
```
SeednRoot.py PlateSplitter_output_SeednRoot_input/
```
For more info run:
```
SeednRoot.py -h
```