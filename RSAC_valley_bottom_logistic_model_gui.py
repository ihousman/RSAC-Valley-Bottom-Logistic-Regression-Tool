#Tool written by: Ian Housman
#USDA Forest Service Remote Sensing Applications Center, Salt Lake City, UT
#Contact: ihousman@fs.fed.us
#
#Tool serves as a gui for the valley bottom logistic model script
################################################################################################
from RSAC_valley_bottom_logistic_model import *
from Tkinter import *
import os, sys
from tkFileDialog import askopenfilename
from tkFileDialog import askopenfilenames
from tkFileDialog import askdirectory
from tkSimpleDialog import askstring
from tkMessageBox import showwarning
import tkMessageBox
from tkFileDialog import asksaveasfilename

cwd = os.getcwd()
cwd = cwd.replace('\\', '/') + '/'

wd = cwd + 'temp/'
if os.path.exists(wd) == False:
    os.makedirs(wd)
idir = ''
################################################################################################
#Select the training point shapefile
def select_shp():
    #Tries to set the initial dir to the current input directory or output directory
    if idir == '':
        idir = os.path.dirname(in_shpe.get())

    if len(idir) == 0:
        idir = cwd

    shp = str(askopenfilename(title = 'Select Predictor Point Shapefile', initialdir = idir,filetypes=[("SHAPEFILE","*.shp")]))
    global idir
    idir = os.path.dirname(shp)
    print 'You selected:', shp
    if shp != '':
        global in_shpe
        in_shpe.destroy()
        in_shpe = Entry(root, width = len(shp))
        in_shpe.grid(row = 3, column = 1, columnspan = 2, sticky = W)
        in_shpe.insert(0, shp)
######################################################################
#Select the dem to work with
def select_dem():
    #Tries to set the initial dir to the current input directory or output directory
    if idir == '':
        idir = os.path.dirname(in_deme.get())

    if len(idir) == 0:
        idir = cwd

    dem = str(askopenfilename(title = 'Select DEM raster', initialdir = idir,filetypes=[("IMAGINE","*.img"),("tif","*.tif"), ('All Files', '*.*')]))
    global idir
    idir = os.path.dirname(dem)
    print 'You selected:', dem
    if dem != '':
        global in_deme
        in_deme.destroy()
        in_deme = Entry(root, width = len(dem))
        in_deme.grid(row = 1, column = 1, columnspan = 2, sticky = W)
        in_deme.insert(1, dem)

######################################################################
#Select output image name
def select_out_vb():
    if idir == '':
        idir = os.path.dirname(out_vbe.get())
    #if len(idir) == 0:
        #idir = os.path.dirname(i.get())
    if len(idir) == 0:
        idir = cwd

    image =  str(asksaveasfilename(title = 'Select output vb prob name',initialdir = idir, filetypes=[("IMAGINE","*.img"),("tif","*.tif")]))
    if image != '':
        if os.path.splitext(image)[1] == '':
            image += '.img'
    global idir
    idir = os.path.dirname(image)
    global out_vbe
    out_vbe.destroy()
    out_vbe = Entry(root, width = len(image))
    out_vbe.insert(0, image)
    out_vbe.grid(row = 5, column = 1, columnspan = 2, sticky = W)


######################################################################
#Select the predictor variable directory
def select_pred_dir():
    #prt = pre.get()
    if idir == '':
        pd = pred_dire.get()
        idir = pd
    if idir == '':
        idir = cwd

    dirname = askdirectory(initialdir = idir, title = 'Select Predictor Output Directory')
    global pred_dire

    global idir
    idir = os.path.dirname(dirname)
    if dirname[-1] != '/':
        dirname += '/'
    pred_dire.destroy()
    pred_dire = Entry(root, width = len(dirname))
    pred_dire.insert(0, dirname)
    pred_dire.grid(row = 2, column = 1, columnspan = 2, sticky = W)


######################################################################
#Refreshes the check boxes with any .tif or .img found in the predictor variable directory
def refresh_preds():
    pred_dir = pred_dire.get()
    extension_list = ['.tif', '.img', '.TIF']
    global predictors
    predictors = glob(pred_dir, extension_list)
    #print predictors
    l = Label(root, text = 'Please check any wanted predictors\nAdd any predictors (.tif or .img) to the Predictor Directory\n and refresh by hitting Refresh Predictors')
    l.grid(row = 1, column = 5, rowspan = 2,sticky = W)

    try:
        for ci in ci_list:
            ci.destroy()
    except:
        print ''
    global states, ci_list
    states = []
    ci_list = []
    rf = 3


    for pred in predictors:
        var2 = IntVar()
        c = Checkbutton(root, text = os.path.basename(pred), variable = var2)
        c.var = var2
        #c.invoke()
        c.grid(row = rf, column = 5, sticky = W)
        states.append(var2)
        ci_list.append(c)
        rf += 1


######################################################################
#Prepares some common topographic indices that work well at predicting valley bottom areas
def prepare_preds():
    in_dem = in_deme.get()
    pred_dir = pred_dire.get()
    if pred_dir[-1] != '/':
        pred_dir += '/'
    flow_init = int(fl.get())
    print in_dem
    print pred_dir
    if os.path.exists(in_dem) == False:
        warning = showwarning('DEM does not exist!', 'Please select an existing DEM')
    if os.path.exists(pred_dir) == False:
        os.makedirs(pred_dir)
    if os.path.exists(in_dem):
        vb_prep(in_dem, pred_dir, flow_initiation_threshold = flow_init)

        refresh_preds()


######################################################################
#Runs the logistic regression model with the checked predictor variables
def run_logistic_model():
    try:
        check_values =  map((lambda var: var.get()), states)
        i = 0
        checked_preds = []
        for pred in predictors:
            if check_values[i] == 1:
                checked_preds.append(pred)
            i += 1
        output = out_vbe.get()
        pred_shp = in_shpe.get()
        vb_field = predictor_fielde.get()
        print output
        print pred_shp
        print vb_field
        print checked_preds
        vb_logistic_model(output, checked_preds, pred_shp, vb_field = vb_field)
    except:
        refresh_preds()
        warning = showwarning('Select Predictors!', 'Must select predictors first')
################################################################################################
def default_logistic_model():
    pred_keys = ['Height_Above_Channel', 'Euc_times_Slope']
    coeffs = [47.9956401079, -2.68893901631, -2.38534146141]
    pred_list = []
    for key in pred_keys:
        for pred in predictors:

            if pred.find(key) > -1:
                pred_list.append(pred)
    if len(pred_list) == len(pred_keys):
        out = os.path.splitext(out_vbe.get())[0] + '_default_model' + os.path.splitext(out_vbe.get())[1]
        apply_logit(out, coeffs, pred_list)
    else:
        warning = showwarning('Prepare Predictors!', 'Please run prepare predictors to\nensure default predictors exist')
    print
    print
    print 'Completed running default logistic regression model'
################################################################################################
################################################################################################
#Set up the gui window
popup = 't_root'
root = Tk()
root.title('RSAC Valley Bottom Logistic Regression Tool')
root.geometry("+0+0")
try:
    root.iconbitmap(default =  cwd + 'VB_logo.ico')
except:
    print 'No icon found'
top = Menu(root)
root.config(menu = top)
################################################################################
#Default parameters
#Change in order to avoid reselecting each time the program is used
default_dem = cwd + 'test_data/small_teton_dem.img'
default_shp = cwd + 'test_data/teton_test.shp'
default_out_vb = cwd + 'test_outputs/vb_test.img'
default_pred_dir = cwd + 'test_output_predictors/'
default_predictor_field = 'VB'
################################################################################
button_start_column = 0
label_start_column = 3
start_row = 1
path_list = [
             ['button','in_dem','1. Input DEM', 'select_dem', '1', button_start_column, 'default_dem'],
             ['button','pred_dir', '1. Predictor Directory', 'select_pred_dir', '2', button_start_column, 'default_pred_dir'],
             ['button','in_shp', '2. Predictor Shapefile', 'select_shp', '3', button_start_column, 'default_shp'],
             ['label','predictor_field', '2. Predictor Field Name', '', '5', button_start_column, 'default_predictor_field'],
             ['button','out_vb', '2. Output VB Prob Name', 'select_out_vb', '4', button_start_column, 'default_out_vb'],
             ['just_button', 'prep', '1. Prepare Predictors', 'prepare_preds', '6', label_start_column, ''],
             ['just_button', 'log_model', '2. Logistic Regression Model', 'run_logistic_model', '8', label_start_column, ''],
             ['just_button', 'default_model', 'Default Model (optional)', 'default_logistic_model', '7', label_start_column, ''],
             ['just_button', 'refresh', 'Refresh Predictors', 'refresh_preds', '6', label_start_column, '']
             ]

for pth in path_list:
    if pth[0].find('button') > -1:
        exec(pth[1] + 'b = Button(root, text = "'+ pth[2] +'", height = 1, width = len("'+ pth[2] +'"), command = '+pth[3]+')')
        exec(pth[1] + 'b.grid(row = ' + str(start_row) + ', column = '+str(pth[5])+', sticky = E, padx = 3, pady = 1)')
    else:
        exec(pth[1] + 'l = Label(root, text = "' + pth[2] + '")')
        exec(pth[1] + 'l.grid(row = ' + str(start_row) + ', column = '+str(pth[5])+', sticky = E, padx = 3)')
    if pth[0].find('just') == -1:
        exec(pth[1] + 'e = Entry(root, width = len(' + pth[-1] + ')+3)')
        exec(pth[1] + 'e.insert(0, ' + pth[-1] + ')')
        exec(pth[1] + 'e.grid(row = ' +str(start_row) + ', column = '+str(int(pth[5]) + 1)+', columnspan = 1, sticky = W)')

    rl = int(pth[4])
    start_row += 1

rl += 0
l = Label(root, text = '                    1. Flow initiation\n                    threshold (sq m)')
l.grid(row = 2, column = 3, rowspan = 2, sticky = W)
fl = Scale(root, from_=1000, to=500000,resolution = 100, orient=VERTICAL)
fl.set(150000)
fl.grid(row = 1, column =3, rowspan = 4, sticky = W)


################################################################################
b = Button(root, text = "Exit", height = 1, width = 10, command = sys.exit)
b.grid(row = rl + 4, column = 6, sticky = S)
root.mainloop()
