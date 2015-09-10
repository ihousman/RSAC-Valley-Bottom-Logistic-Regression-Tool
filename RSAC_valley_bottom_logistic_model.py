#Tool written by: Ian Housman
#USDA Forest Service Remote Sensing Applications Center, Salt Lake City, UT
#Contact: ihousman@fs.fed.us

#Tool was re-written from its original version on 12-27-12 to serve as a stand-alone tool using Arc10 and R 2.11
#Original tool was written with funds from a FY 2011 Remote Sensing Steering Committee project for mapping riparian
#vegetation on the GMUG NFs.

#Tool was updated on 12-16-13 to run without rpy2.  This ensures compatability with > Python 2.6

#Tool is intended to be used as a logistic regression-based valley bottom model
#The tool prepares several common topographic predictor variables and then creates a valley bottom probability
#layer using a provided binary (1 = valley bottom, 0 = upland) training point shapefile
###############################################################################
#Import all necessary packages
import shutil, os, subprocess, sys, string, random, math, time, itertools, urllib, zipfile
from tkFileDialog import askopenfilename
from dbfpy import dbf
import numpy, time
###############################################################################
#Find the current working directory
cwd = os.getcwd()
cwd = cwd.replace('\\', '/') + '/'
###############################################################################
#Set Python version and home directory
python_possibilities = {'C:\\Python27\\ArcGIS10.2': [27, 10.2],'C:\\Python27\\ArcGIS10.1': [27, 10.1], 'C:\\Python26\\ArcGIS10.0': [26, 10]}#, 'C:\\Python26': [26, 9.3],'C:\\Python25' : [25, 9.3]}
for possibility in python_possibilities:
    if os.path.exists(possibility):
        arc_version = python_possibilities[possibility][1]
        python_version =   python_possibilities[possibility][0]
        python_dir = possibility
        #break
###############################################################################
#Set up the gdal data and bin environment variable names
site_packages_dir = python_dir + '/Lib/site-packages/'
gdal_data_options = [site_packages_dir + 'gdalwin32-1.6/data', site_packages_dir + 'gdalwin32-1.9/bin/gdal-data']
gdal_bin_options = [site_packages_dir + 'gdalwin32-1.6/bin', site_packages_dir + 'gdalwin32-1.9/bin']
gdal_data_dir = ''
gdal_bin_dir = ''
for data_option in gdal_data_options:
    if os.path.exists(data_option):
        gdal_data_dir = data_option
for bin_option in gdal_bin_options:
    if os.path.exists(bin_option):
        gdal_bin_dir = bin_option
###############################################################################
#Let user know what the directories are
#(Arc version does not necessarily mean that Arc is installed)
print 'Arc version:',arc_version
print 'Python version:', python_version
print 'Python dir:', python_dir
print 'GDAL bin:', gdal_bin_dir
print 'GDAL data:', gdal_data_dir

python_version_dec = str(float(python_version)/10)
python_version = str(python_version)
admin = False
##############################################################################################
#Returns all files containing an extension or any of a list of extensions
#Can give a single extension or a list of extensions
def glob(Dir, extension):
    if type(extension) != list:
        if extension.find('*') == -1:
            return map(lambda i : Dir + i, filter(lambda i: os.path.splitext(i)[1] == extension, os.listdir(Dir)))
        else:
            return map(lambda i : Dir + i, os.listdir(Dir))
    else:
        out_list = []
        for ext in extension:
            tl = map(lambda i : Dir + i, filter(lambda i: os.path.splitext(i)[1] == ext, os.listdir(Dir)))
            for l in tl:
                out_list.append(l)
        return out_list
##############################################################################################
#Returns all files containing a specified string (Find)
def glob_find(Dir, Find):
    return map(lambda i : Dir + i, filter(lambda i:i.find(Find) > -1, os.listdir(Dir)))
##############################################################################################
#Returns all files ending with a specified string (end)
def glob_end(Dir, end):
    return map(lambda i : Dir + i, filter(lambda i:i[-len(end):] == end, os.listdir(Dir)))
##############################################################################################
###############################################################################
##r_version_dict = {'2.6': '11', '2.5':'11', '2.7': '12'}
##r_version = r_version_dict[python_version_dec]
##print 'R version:', r_version
###############################################################################
#Find the program files dir
program_files_dir_options = ['C:/Program Files (x86)/', 'C:/Program Files/']
for option in program_files_dir_options:
    if os.path.exists(option):
        program_files_dir = option
        break
print 'Program files dir:', program_files_dir
###############################################################################
#Find rscript.exe
#If your R directory is not in the r_dir_options, add it to the list
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
        warning = showwarning('Could not find R', 'Please ensure a version of R is installed\nIf there is one, ensure the directory is under the\nr_dir_options in the RSAC_valley_bottom_logistic_model.py')
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
print 'Rscript.exe:', r_script_exe
###############################################################################
###Set up the R 2.11 path
##os.chdir(program_files_dir + '/R/R-2.'+r_version+'.1/bin')
##path = os.getenv('PATH')
##if path[-1] != ';':
##    path += ';'
##r_home = program_files_dir.replace('/', '\\') + 'R\\R-2.'+r_version+'.1'
##win32com_path = python_dir + '\\Lib\\site-packages\\win32'
##sys.path.append(win32com_path)
##path = path + r_home
##os.putenv('PATH',path)
##os.putenv('R_HOME',r_home)
###os.putenv('Rlib',os.path.split(r_home)[0] + '\\library')
##print 'r_home:',r_home
##print os.getenv('R_HOME')
###Import rpy2
##import rpy2.robjects as RO
##import rpy2.robjects.numpy2ri
##r = RO.r
##os.chdir(cwd)
###############################################################################
if arc_version > 9.3:#== 10 or arc_version == 10.1:
    print 'Using arcpy'
    import arcpy as gp
    from arcpy import env
    from arcpy.sa import *
    gp.CheckOutExtension("Spatial")


    wd = cwd + 'temp/'
    if os.path.exists(wd) == False:
        os.makedirs(wd)
    env.workspace = wd
    gp.OverwriteOutput = True
elif python_version == 26:
    print '*****Using Python 26 to run this script*****'
    print''
    print''
    #Import system modules
    import sys, string
    #the next two lines are required if you have ever uninstalled the Python that came with ArcGIS and put a new one on
    from dbfpy import dbf
    from win32com.client import Dispatch
    gp = Dispatch('esriGeoprocessing.GpDispatch.1')

    # Check out any necessary licenses
    gp.CheckOutExtension("spatial")
    gp.CheckOutExtension("3D")
    # Load required toolboxes...
    gp.AddToolbox("C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Spatial Analyst Tools.tbx")
    gp.AddToolbox("C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Data Management Tools.tbx")
    gp.AddToolbox("C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/3D Analyst Tools.tbx")
    gp.AddToolbox("C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Analysis Tools.tbx")
    gp.AddToolbox("C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Conversion Tools.tbx")
    gp.OverWriteOutput = 1
    ### Import system modules

    #################################################################

#Use this for PYTHON 2.5
elif python_version == 25:
    print '*****Using Python 25 to run this script*****'
    print''
    print''
    import arcgisscripting, csv
    from dbfpy import dbf

    # Create the Geoprocessor object
    gp = arcgisscripting.create()

    # Check out any necessary licenses
    gp.CheckOutExtension("spatial")
    gp.CheckOutExtension("3D")
    # Load required toolboxes...
    gp.AddToolbox("C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Spatial Analyst Tools.tbx")
    gp.AddToolbox("C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Data Management Tools.tbx")
    gp.AddToolbox("C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/3D Analyst Tools.tbx")
    gp.AddToolbox("C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Analysis Tools.tbx")
    gp.AddToolbox("C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Conversion Tools.tbx")
    # Set environments
    gp.overwriteoutput = 1
else:
    print 'Must have Python 2.4 or 2.5 installed in order to run this program.  Please download from www.Python.org'
    print''
    raw_input('!!!Press enter to continue!!!')

####################################################################################
########################################################################################
#Function to convert a specified column from a specified dbf file into a list
#e.g. dbf_to_list(some_dbf_file, integer_column_number)
def dbf_to_list(dbf_file, field_name):
    if os.path.splitext(dbf_file)[1] == '.shp':
        dbf_file = os.path.splitext(dbf_file)[0] + '.dbf'
    #The next exception that is handled is handled within an if loop
    #This exception would occur if a non .dbf file was entered
    #First it finds wither the extension is not a .dbf by splitting the extension out
    if os.path.splitext(dbf_file)[1] != '.dbf':
        #Then the user is prompted with what occured and prompted to exit as above
        print 'Must input a .dbf file'
        print 'Cannot compile ' + dbf_file
        raw_input('Press enter to continue')
        sys.exit()

    #Finally- the actual function code body
    #First the dbf file is read in using the dbfpy Dbf function
    db = dbf.Dbf(dbf_file)
    #Db is now a dbf object within the dbfpy class

    #Next find out how long the dbf is
    rows = len(db)

    #Set up a list variable to write the column numbers to
    out_list = []

    #Iterate through each row within the dbf
    for row in range(rows):
        #Add each number in the specified column number to the list
        out_list.append(db[row][field_name])
    db.close()
    #Return the list
    #This makes the entire function equal to the out_list
    return out_list
################################################################
####################################################################################
#Function to prepare several common topographic predictors from a provided DEM
#It assumes the units are meters
def vb_prep(input_dem, output_folder, fill = True, no_data = 0, flow_initiation_threshold = 150000, mask = False):
    #Setup the directories and paths
    intermediate_folder = output_folder + 'Intermediate/'
    if os.path.exists(intermediate_folder ) == False:
        os.makedirs(intermediate_folder)
    out_base = output_folder + os.path.splitext(os.path.basename(input_dem))[0]
    out_int_base = intermediate_folder + os.path.splitext(os.path.basename(input_dem))[0]

    #List of predictors available that will be filled
    predictors = []

    if mask == True:
        masked_out = out_int_base + '_Masked.img'
        if os.path.exists(masked_out) == False:
            print 'Masking no data values'
            outCon = Con(input_dem, input_dem, "","VALUE > " + str(no_data))
            outCon.save(masked_out)
            del outCon
    else:
        masked_out = input_dem

    #Fill the dem
    dem_fill = out_int_base + '_Fill.img'
    if os.path.exists(dem_fill) == False:
        print 'Filling DEM', input_dem
        print
        outFill = Fill(masked_out)
        outFill.save(dem_fill)
        del outFill

    #Find some basic info about teh filled dem for use in subsequent steps
    info = gp.Describe(dem_fill)
    res = info.meanCellHeight

    #Calculates the hillshade
    hillshade = out_int_base + '_hillshade.img'
    if os.path.exists(hillshade) == False:
        print 'Calculating the hillshade of', dem_fill
        print
        outHillShade = gp.sa.Hillshade(dem_fill, 315, 45, "SHADOWS", 1)
        outHillShade.save(hillshade)
        del outHillShade
    #Calculate the flow direction
    dem_flow_dir = out_int_base + '_Flow_Dir.img'
    if os.path.exists(dem_flow_dir) == False:
        print 'Calculating DEM flow direction from', dem_fill
        print
        outFlowDir = FlowDirection(dem_fill)
        outFlowDir.save(dem_flow_dir)
        del outFlowDir
    #Calculate the flow accumulation area in square units (assumed to be meters)
    dem_flow_acc = out_int_base + '_Flow_Accumulation_sq_m.img'
    if os.path.exists(dem_flow_acc) == False:
        print 'Calculating DEM flow accumulation from', dem_flow_dir
        print
        outFlowAcc = FlowAccumulation(dem_flow_dir) * res * res
        outFlowAcc.save(dem_flow_acc)
        del outFlowAcc

    #Creates the drainage network by thresholding the flow accumulation layer
    dem_drainage_network = out_int_base + '_Drainage_Network.img'
    if os.path.exists(dem_drainage_network) == False:
        print 'Thresholding the DEM drainage network from', dem_flow_acc
        print
        outCon2 = Con(dem_flow_acc, "1", "", "VALUE > " + str(flow_initiation_threshold))
        outCon2.save(dem_drainage_network)
        del outCon2
    #Converts the raster drainage network to a vector (this is never used in the actual model)
    dem_drainage_network_shp = out_int_base + '_Drainage_Network_s.shp'
    if os.path.exists(dem_drainage_network_shp) == False:
        print 'Converting raster DEM drainage network to a shapefile'
        print
        outPoly = gp.RasterToPolyline_conversion(dem_drainage_network, dem_drainage_network_shp)
        del outPoly

    #Computes the Strahler stream order
    stream_order = out_int_base + '_Strahler_Stream_Order.img'
    if os.path.exists(stream_order) == False:
        print 'Computing the Strahler stream order'
        print
        outSO = StreamOrder(dem_drainage_network, dem_flow_dir, "STRAHLER")
        outSO.save(stream_order)
        del outSO
    #Computes the stream links
    stream_link = out_int_base + '_Stream_Links.img'
    if os.path.exists(stream_link) == False:
        print 'Creating stream links'
        print
        SL = StreamLink(dem_drainage_network, dem_flow_dir)
        SL.save(stream_link)
        del SL
    #Creates watersheds
    watersheds = out_int_base + '_Watersheds.img'
    if os.path.exists(watersheds) == False:
        print 'Identifying watersheds'
        print
        WS = Watershed(dem_flow_dir, stream_link, "VALUE")
        WS.save(watersheds)
        del WS
    #All subsequent variables are predictor variables
    #Computes the slope in radians (percent/100) and smooths it using a 6x6 circular kernel to reduce artifacts
    slope_radians = out_base + '_Slope_Radians.img'
    predictors.append(slope_radians)
    if os.path.exists(slope_radians) == False:
        print 'Calculating radian slope from', dem_fill
        print
        neighborhood = NbrCircle(3, "CELL")
        slpRad = Slope(dem_fill, "PERCENT_RISE")/100.0
        slpRadSmth = FocalStatistics(slpRad, neighborhood, "MEAN")
        slpRadSmth.save(slope_radians)
        del slpRad
        del slpRadSmth
##    #Computes curvature
##    curvature = out_base + '_Curvature.img'
##    plan_curve = out_base + '_Plan_Curvature.img'
##    profile_curve = out_base + '_Profile_Curvature.img'
##    predictors.append(curvature)
##
##    if os.path.exists(curvature) == False:
##        print 'Calculating curvature'
##        print
##        curv = Curvature(dem_fill, 1, profile_curve, plan_curve)
##        neighborhood = NbrCircle(2, "CELL")
##        curvSmth = FocalStatistics(curv, neighborhood, "MEAN")
##        curvSmth.save(curvature)

    #Computes the height above channel (assumed to be in meters)
    hac = out_base + '_Height_Above_Channel.img'
    predictors.append(hac)
    if os.path.exists(hac) == False:
        print 'Calculating the height above the channel'
        print
        outHAC = CostDistance(dem_drainage_network, slope_radians)
        outHAC.save(hac)
        del outHAC
    #Computes teh euclidean distance from the channel
    euc = out_base + '_Euclidean_Distance_from_Channel.img'
    predictors.append(euc)
    if os.path.exists(euc) == False:
        print 'Calculating the euclidean distance from channel'
        print
        outEuc = EucDistance(dem_drainage_network, cell_size = res)
        outEuc.save(euc)
        del outEuc
    #Computes the product of the euclidean distance and slope (slightly different from the height above the channel)
    eucxslope = out_base + '_Euc_times_Slope.img'
    predictors.append(eucxslope)
    if os.path.exists(eucxslope) == False:
        print 'Multplying the euclidean distance by the slope'
        print
        outEucxSlope = Times(euc, slope_radians)
        outEucxSlope.save(eucxslope)
        del outEucxSlope
    #Computes the topographic position index (TPI)
    #Difference in elevation between a pixel and the average of its neighborhood
    #Currently uses a circular kernel of varying diameters
    #The z suffix indicates that it is the z score of the elevation within a given neighborhood
    tpis = [20,30,40, 60]
    for tpi in tpis:
        tpi_out = out_base + '_TPI_'+str(tpi)+'.img'
        tpi_outz = out_base + '_TPI_'+str(tpi)+'z.img'
        predictors.append(tpi_out)
        predictors.append(tpi_outz)
        if os.path.exists(tpi_out) == False or os.path.exists(tpi_outz) == False:
            neighborhood = NbrCircle(tpi/2, "CELL")
            print 'Computing the topographic position index neighborhood', tpi
            print
            mean = FocalStatistics(dem_fill, neighborhood, "MEAN")
            std = FocalStatistics(dem_fill, neighborhood, "STD")
            tpir = dem_fill - mean
            tpir.save(tpi_out)
            del tpir
            tpizr = (dem_fill - mean)/std
            tpizr.save(tpi_outz)
            del mean
            del std
            del tpizr
    #Computes the compound topographic wetness index (CTWI) and smooths it using a 14x14 circular kernel
    ctwi = out_base + '_CTWI.img'
    predictors.append(ctwi)
    if os.path.exists(ctwi) == False:
        print 'Computing the compound topographic wetness index'
        print
        acc = Raster(dem_flow_acc)
        slp = Raster(slope_radians)
        neighborhood = NbrCircle(7, "CELL")
        ctwi_out = FocalStatistics(Ln((acc + 1) * 100 / Tan((slp) + 0.001)), neighborhood, "MEAN")
        ctwi_out.save(ctwi)
        del acc
        del slp
        del ctwi_out
    print
    print
    print 'The predictors are:'
    for predictor in predictors:
        print os.path.basename(predictor)
    print
    print
    print 'Valley bottom prep is complete'
    return predictors
##############################################################################
#Function to set up a table of a binary training column and predictor columns with a specified point training
#shapefile and a list of raster predictor variables
def logistic_table_setup(pred_shp, predictors, predictor_table_name = '', raster_field_name = 'RASTERVALU', vb_field = 'VB'):
    #Set up a temp folder for processing
    #Use the local time to create a unique folder name
    #This ensures that the most up-to-date points are used
    ts = time.localtime()
    timeStr = ''
    for t in ts[:6]:
        print t
        timeStr += str(t) + '_'
    timeStr = timeStr[:-1]
    t_folder = os.path.dirname(predictor_table_name) + '/predictor_points_' +timeStr + '/'
    print 'T_folder is', t_folder

    try:
        if os.path.exists(t_folder):
            os.removedirs(t_folder)
    except:
        print 'Could not remove', t_folder
    if os.path.exists(t_folder) == False:
        os.makedirs(t_folder)

    #Set up the table and fill it in by extracting the raster values from each point
    out_table = []
    for pred in predictors:
        out_shp = t_folder + os.path.splitext(os.path.basename(pred))[0] + '.shp'

        print 'Extracting raster values from', pred
        runNum = 0
        if os.path.exists(out_shp) == False:
            ExtractValuesToPoints(pred_shp, pred, out_shp, 'INTERPOLATE', 'VALUE_ONLY')

        if os.path.exists(out_shp) == False:
            warning = showwarning('Could not extract values', 'Could not extract values of ' + pred )
        else:
            values = dbf_to_list(out_shp, raster_field_name)
            out_table.append(values)

    #Extract the training values
    vb = dbf_to_list(pred_shp, vb_field)

    #Create the final tab-delimited table
    final_table = vb_field
    for pred in predictors:
        final_table += '\t' + os.path.basename(pred)
    final_table += '\n'
    for i in range(len(vb)):
        final_table += str(vb[i]) + '\t'
        for column in out_table:
            final_table += str(column[i]) + '\t'
        final_table = str(final_table[:-1]) + '\n'

    #Give the table a name and write it
    if predictor_table_name == '':
        tof = t_folder + 'predictor_table.txt'
    else:
        tof = predictor_table_name
    tofd = os.path.dirname(tof)
    if os.path.exists(tofd) == False:
        os.makedirs(tofd)
    tofo = open(tof, 'w')
    tofo.writelines(final_table)
    tofo.close()

    print 'Finished creating', tof
    return tof
##############################################################################
#Takes a tab-delimited .txt file and finds the coefficients that correspond to the logit function of that table
#This uses rpy2 to interact with R 2.11 through Python
def logistic_model(predictor_table, pred_field_name = 'VB', name_prefix = ''):
    #Read in the predictor table
    table = r('pred_table = read.delim("' + predictor_table + '", header = TRUE)')
    r('attach(pred_table)')

    #Concatenate the string to pass into R's glm
    glm_string = ''
    names = list(r('names(pred_table)'))
    for name in names:
        if name != pred_field_name:
            glm_string += name + ' + '
    glm_string = glm_string[:-3]

    #Call on R's glm (generalized linear model) to get the coefficients
    r('result = glm(' + pred_field_name + '~ ' + glm_string + ', family = binomial("logit"))')
    results = r.get('result')
    print str(results)

    #Produce a plot for each fitted predictor
    devoff = RO.r['dev.off']
    for name in names[1:]:
        print name
        png_f = os.path.dirname(predictor_table) + '/' + name_prefix +  name + '_plot.png'
        r.png(png_f)
        r('plot(' + name + ', fitted(result), xlab = "' + name + '", ylab = "Prob", main = "Fitted ' + name + '")')
        devoff()

    #Write out the results to a text file
    rof = os.path.splitext(predictor_table)[0] + '_results.txt'
    ro = open(rof, 'w')
    ro.writelines(str(results))
    ro.close()

    #Get the coefficients and return them
    coeffs = list(r('coefficients(result)'))
    return coeffs

##############################################################################
def logistic_model_rscript(predictor_table, pred_field_name = 'VB', name_prefix = '', run = True):
    r_file = os.path.splitext(predictor_table)[0] + '_rscript.r'
    bat_file = os.path.splitext(r_file)[0] + '_bat.bat'
    rls = ''
    #Read in the predictor table
    rls += 'pred_table = read.delim("' + predictor_table + '", header = TRUE)\n'
    #table = r('pred_table = read.delim("' + predictor_table + '", header = TRUE)')

    rls += 'attach(pred_table)\n'
    #r('attach(pred_table)')

    #Concatenate the string to pass into R's glm
##    glm_string = ''
##    names = list(r('names(pred_table)'))
##    for name in names:
##        if name != pred_field_name:
##            glm_string += name + ' + '
##    glm_string = glm_string[:-3]

    #Call on R's glm (generalized linear model) to get the coefficients
    rls += 'result = glm(' + pred_field_name + '~., data = pred_table, family = binomial("logit"))\n'
    #r('result = glm(' + pred_field_name + '~ ' + glm_string + ', family = binomial("logit"))')


    #results = r.get('result')
    #print str(results)
    rls += 'print(result)\n'
    rof = os.path.splitext(predictor_table)[0] + '_results.txt'
    rls += 'results_file = "' + rof + '"\n'
    #Produce a plot for each fitted predictor
    #rls +=
    #devoff = RO.r['dev.off']
##    for name in names[1:]:
##        print name
##        png_f = os.path.dirname(predictor_table) + '/' + name_prefix +  name + '_plot.png'
##        rls += 'png("' + png_f + '")\n'
##        #r.png(png_f)
##
##        rls += 'plot(' + name + ', fitted(result), xlab = "' + name + '", ylab = "Prob", main = "Fitted ' + name + '")'
##        #r('plot(' + name + ', fitted(result), xlab = "' + name + '", ylab = "Prob", main = "Fitted ' + name + '")')
##
##        rls += 'dev.off()\n'
    rls+= 'for (name in names(pred_table)[-1]){\n'
    rls += '\tprint(paste("Plotting: ",name,sep = ""))\n'
    rls += '\tpng_f = paste(results_file, "_", name , "_plot.png", sep = "")\n'
    rls += '\tpng(png_f)\n'
    rls += '\tplot(eval(parse(text = name)), fitted(result), xlab = name, ylab = "Prob", main = paste("Fitted ", name, sep = ""))\n'
    rls += '\tdev.off()\n'
    rls += '}\n'
        #devoff()

    #Write out the results to a text file

    #ro = open(rof, 'w')
    #ro.writelines(str(results))
    #ro.close()

    rls += 'out = capture.output(summary(result))\n'
    rls += 'cat(out, file = results_file, sep = "'+str('\n') + '")\n'
##    rls += 'fileConn = file("' + rof + '")\n'
##    rls += 'writeLines(result, fileConn)\n'
##    rls += 'close(fileConn)\n'


    #Get the coefficients and return them
    rls += 'out_c = t(data.frame(coefficients(result)))\n'


    coeffs_file = os.path.splitext(predictor_table)[0] + '_coeffs.csv'
    rls += 'write.table(out_c, "'+coeffs_file+'", quote = FALSE, sep = ",", col.names = NA)\n'
    #coeffs = list(r('coefficients(result)'))
    #return coeffs
    rls += 'detach(pred_table)\n'

    rof = open(r_file, 'w')
    rof.writelines(rls)
    rof.close()

    b_lines = r_script_exe[:2] + '\ncd ' + os.path.dirname(r_script_exe) + '\n'
    b_lines += os.path.basename(r_script_exe) + ' "' + r_file + '"\n'

    obo = open(bat_file, 'w')
    obo.writelines(b_lines)
    obo.close()
    if run:
        try:
            call = subprocess.Popen(bat_file)
            call.wait()
        except:
            print 'Encountered error while running:', bat_file
    if os.path.exists(coeffs_file):
        cfo = open(coeffs_file, 'r')
        cfls = cfo.readlines()
        cts = cfls[1].split(',')[1:]
        cfo.close()

        out_coeffs = []
        cts[-1] = cts[-1][:-1]
        for ct in cts:
            out_coeffs.append(float(ct))
        return out_coeffs
##############################################################################
#Takes a set of coefficients and applies them to the logit function and writes out a raster
def apply_logit(output, coefficients, predictors):
    od = os.path.dirname(output)
    if os.path.exists(od) == False:
        os.makedirs(od)

    #Set up the string to be called
    intercept = coefficients[0]
    coefficients = coefficients[1:]
    string = str(intercept) + ' + ('
    for i in range(len(coefficients)):
        string += str(float(coefficients[i])) + ' * Raster("' + str(predictors[i]) + '")) + ('
    string = string[:-4]

    #Call on the string and save it to a raster
    print
    print 'The logit string is'
    print '1.0/(1.0 + Exp(-1.0 * ' + string + '))'
    print
    print 'Computing', output
    fp = eval(string)
    lp = 1.0 / (1.0 + Exp(-1.0 * fp))
    lp.save(output)
##############################################################################
#Sets up the predictors and calls on each individual component of the model
def vb_logistic_model(output, predictor_folder, pred_shp = None, extension_list = ['.tif', '.img', '.TIF'], vb_field = 'VB'):
    if type(predictor_folder) == list:
        predictors = predictor_folder
    elif os.path.isdir(predictor_folder):
        predictors = glob(predictor_folder, extension_list)
    else:
        predictors = [predictor_folder]


    if pred_shp == None or os.path.exists(pred_shp) == False:
        pred_shp = str(askopenfilename(title = 'Select Predictor Shapefile',filetypes=[("SHAPEFILE","*.shp")]))
    pred_table_name = os.path.splitext(output)[0] + '_predictor_table.txt'
    pred_table = logistic_table_setup(pred_shp, predictors, pred_table_name, vb_field = vb_field)
    coeffs = logistic_model_rscript(pred_table, pred_field_name = vb_field, name_prefix = os.path.basename(output) + '_')
    apply_logit(output, coeffs, predictors)

    print
    print
    print 'Completed creating', output
##############################################################################
#Preliminary development of an interactive stream visualization package (currently not implemented)
##class stream_vis:
##    global plt
##    from matplotlib.widgets import Slider, Button, RadioButtons, SpanSelector
##    import matplotlib.pyplot as plt
##    #from matplotlib_lib import *
##    def __init__(self, in_flow_acc, initial_thresh = 150000):
##        print in_flow_acc
##        self.in_flow_acc = in_flow_acc
##        self.array = gp.RasterToNumPyArray(self.in_flow_acc)
##        self.thresh = initial_thresh
##
##    def display_image(self):
##        t =  self.array
##        t[t > self.thresh] = 1
##        t[t < self.thresh] = 0
##        print self.array
##        print 'Unique values:', numpy.unique(self.array)
##        self.l22 = plt.subplot2grid(shape = (1,1), loc = [0,0])
##        plt.show()
##        nm = imshow(t)
##        show()
##        #nm.set_clim((
##
##
##        #t = None
##        #del t
##        #array = None
##        #del array
##############################################################################
##############################################################################
#in_dir = 'C:/Valley_Bottom_Logistic_Model/inputs/'
##out_dir = 'C:/Valley_Bottom_Logistic_Model/outputs/'
#in_dem = in_dir + 'TaylorRv_Watershed_Project_subset_dem_clp.img'
#in_dir = 'C:/Valley_Bottom_Logistic_Model/outputs10_pred3/Intermediate/TaylorRv_Watershed_Project_subset_dem_clp_Flow_Dir.img'
#in_acc = 'C:/Valley_Bottom_Logistic_Model/outputs/Intermediate/TaylorRv_Watershed_Project_subset_dem_clp_Flow_Accumulation.img'
#sv = stream_vis(in_acc)
#sv.display_image()
##pred_shp = in_dir + 'TaylorRv_Watershed_Project_subset_training1.shp'
##output = out_dir + 'vb_test.img'
###vb_prep(in_dem, out_dir)
##vb_logistic_model(output, out_dir, pred_shp)
#pred_tab = 'D:/Valley_Bottom_Logistic_Model/update/test_outputs/vb_test_predictor_table.txt'
#logistic_model_rscript(pred_tab, pred_field_name = 'VB', name_prefix = '')
