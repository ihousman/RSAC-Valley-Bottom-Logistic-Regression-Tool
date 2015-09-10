import os,sys,shutil,urllib, subprocess
cwd = os.getcwd().replace('\\','/') + '/'
#os.getcwd
###############################################################################
def find_r_script_exe():
    #Find rscript.exe
    #If your R directory is not in the r_dir_options, add it to the list
    r_dir_options = ['C:/Program Files (x86)/R/', 'C:/Program Files/R/']
    r_dir = ''
    r_script_exe = ''
    i = 0
    while r_dir == '' and i < len(r_dir_options):
        rdot = r_dir_options[i]
        if os.path.exists(rdot):
            r_dir = rdot
        i += 1
    if r_dir == '':
        x = 1
        #warning = showwarning('Could not find R', 'Please ensure a version of R is installed\nIf there is one, ensure the directory is under the\nr_dir_options in the RSAC_valley_bottom_logistic_model.py')
    else:
        i = 0
        r_version_dirs = map(lambda i : rdot + i,os.listdir(rdot))

        while r_script_exe == '' and i < len(r_version_dirs):
            texe = r_version_dirs[i] + '/bin/Rscript.exe'
            if os.path.exists(texe):
                r_script_exe = texe
            i += 1
        #print 'r_script_exe',r_script_exe
    return r_script_exe, r_dir
r_script_exe, r_dir = find_r_script_exe()

###############################################################################
dbfpy_url = ['http://sourceforge.net/projects/dbfpy/files/dbfpy/2.2.5/dbfpy-2.2.5.win32.exe/download', 'dbfpy-2.2.5.win32.exe']
r_url =  ['http://cran.r-project.org/bin/windows/base/old/3.0.1/R-3.0.1-win.exe', 'R-3.0.1-win.exe']

if r_script_exe =='':

    exe = cwd + r_url[-1]
    url = r_url[0]
    if os.path.exists(exe) == False:
        print 'Downloading', exe
        File = urllib.urlretrieve(url, exe)
    print 'Running', exe
    call = subprocess.Popen(exe)
    call.wait()
else:
    print 'Installed rscript.exe:', r_script_exe

try:
    import dbfpy
    print 'Successfully imported dbfpy'
except:
    exe = cwd + dbfpy_url[-1]
    url = dbfpy_url[0]
    if os.path.exists(exe) == False:
        print 'Downloading', exe
        File = urllib.urlretrieve(url, exe)
    print 'Running', exe
    call = subprocess.Popen(exe)
    call.wait()

    try:
        import dbfpy
        print 'Successfully imported dbfpy'
    except:
        print'Please manually run', exe

raw_input('Press any key to exit')
