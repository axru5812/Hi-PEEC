# README #


### What is this repository for? ###
This repo contains the code for cluster extraction in Hi-PEEC based on the LEGUS cluster extraction script.

### How do I get set up? ###

####Using Git####
The easiest way to get the required folder structure is using __Git__. To do this run the following in a terminal:

```
git clone https://C0gito@bitbucket.org/C0gito/hi-peec.git
```

which will give a copy of the entire source tree in the last stable version, the 'master'  branch. If you want the 
development version of the code which is not guaranteed to work you can then run 

```
git fetch && git checkout devel
```
which will then load the devel branch making your directory mirror that. 

#####Staying up to date:#####
Doing the above means it is easy to stay up to date with the changes in the code. You do this simply by running 
```
git pull
```
in the directory you placed the source files in.

####Without Git####
The second way is to simply download the zip file that is contained in the master branch. Note that this is updated less
often.


###How to run the pipeline###
1. Set up the required folder structure (see [Here](https://bitbucket.org/C0gito/hi-peec/wiki/projectstructure))

3. Check the Hi-PEEC_settings.input file to make sure that the inputs are appropriate.

2. Run ```python Hi-PEEC_pipeline.py``` in a terminal
