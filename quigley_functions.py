import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import os
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pandas as pd
import csv

from nc_processing import *
from analysis import * 

#%matplotlib inline


# define_parameters takes the CMIP6 variable table and runs through each row to find the corresponding
# domain and project for each experiment. Some variables only have daily domains, and some only have monthly,
# but the domain column uses whatever is available (monthly is preferable, except for ISMIP6 variables).
# It takes var as input, so it must be run every time a new variable is selected.

def define_parameters(var):
    
    var_table = pd.read_csv('CMIP6_variables.csv', index_col = 'var') 
    #Reads csv file and sets 'var' as the row index
    #Setting 'var' as the row index makes the table searchable by variable
    
    domain = var_table.at[var,'domain'] #Finds the corresponding domain for that variable
    project = var_table.at[var,'project'] #Ditto for project
    
    data_dir='/home/users/quigley/Projects/geoengineering_summer' #Changed from Pete's directory
    model='UKESM1-0-LL'
    centre='MOHC'
    exp = 'G6sulfur'
    runs=['r1i1p1f2','r4i1p1f2','r8i1p1f2']
    grid='gn'
    season='ANN'
    time_files=1
    dates=['2070-01-01','2100-01-01']
    #These other parameters are mostly constant, but some other functions redefine them where necessary.
    
    return season,dates,data_dir,model,centre,var,domain,exp,project,runs,grid,time_files


# stats returns the mean and standard deviation of the seasonal mean for whatever variable we input.
# It takes the parameters defined in define_parameters(var) and uses Pete's function get_fixed (called in nc_processing.py) to calculate the gridcell area and land fraction. From there, it creates a weighted mean and standard deviation.

def stats(var):
    
    season,dates,data_dir,model,centre,var,domain,exp,project,runs,grid,time_files = define_parameters(var)
    
    # Use the get_fixed() function to return the gridcell area and land fraction for the model we want.
    ds_area, ds_land = get_fixed('MOHC','UKESM1-0-LL','r1i1p1f2') 

    # Let's define a data array for the area weight of the gridcells
    da_weight = ds_area['areacella'] / ds_area['areacella'].sum()
    da_weight = da_weight.rename(new_name_or_name_dict='area_weight')

    # load the arguments into a list then... 
    args=[season,dates,data_dir,model,centre,var,domain,exp,project,runs,grid,time_files]
    ds_mean, ds_std = get_ens_seasonal_mean_std(*args) # ... unpack them into the function.
    
    # multiply each temperature value with its corresponding fraction of total area, then sum to find the global mean.
    return ds_mean, ds_std


# mod_exac uses define_parameters(var) to get the bulk of its parameters, but it redefines some several times to calculate the different scenarios. The historical data requires older dates with no geoengineering and historical GHG levels. The ssp585 data comes from ScenarioMIP; it looks at an intense warming scenario with no mitigation. mod_exac looks at whether the geoengineering scenario is closer (moderated) or further (exacerbated) from the historical data than is the warming scenario. It runs Pete's better_worse_off function twice - once is with the t-test value set == 1, which just says whether it is closer or further, but nothing about the significance. The second time, it is run at a t-test value of 0.05, which determines significance at the 95% level. The proportions of the globe experiencing insignificant moderation and exacerbation are determined by subtracting the significantly mod/exac portions from the total mod/exac portions.

def mod_exac(var):
    season,dates,data_dir,model,centre,var,domain,exp,project,runs,grid,time_files = define_parameters(var)

    # Load G6sulfur ensemble-mean datasets
    exp='G6sulfur'
    project='GeoMIP'
    dates=['2070-01-01','2100-01-01']
    ds_G6sulfur_mean, ds_G6sulfur_std = get_ens_seasonal_mean_std(season, dates, data_dir, model, centre, var, domain, exp, project, runs, grid, time_files=1)# setting time files to zero.

    # Load ssp585 ensemble-mean datasets
    project='ScenarioMIP'
    exp='ssp585'
    dates=['2070-01-01','2100-01-01']
    ds_ssp585_mean, ds_ssp585_std = get_ens_seasonal_mean_std(season, dates, data_dir, model, centre, var, domain, exp, project, runs, grid, time_files=1)# setting time files to zero.

    # Load ssp585 ensemble-mean datasets
    project='CMIP'
    exp='historical'
    dates=['1960-01-01','1990-01-01']
    ds_historical_mean, ds_historical_std = get_ens_seasonal_mean_std(season, dates, data_dir, model, centre, var, domain, exp, project, runs, grid, time_files=1)# setting time files to zero.
    
    # Call my better_worse_off function, passing in the data_arrays for the variable of interest rather than the full datasets.
    better, worse, dunno = better_worse_off(ds_G6sulfur_mean[var], ds_G6sulfur_std[var], ds_ssp585_mean[var], ds_ssp585_std[var], ds_historical_mean[var], ds_historical_std[var], 90, 0.05)
    insig_better, insig_worse, insig_dunno = better_worse_off(ds_G6sulfur_mean[var], ds_G6sulfur_std[var], ds_ssp585_mean[var], ds_ssp585_std[var], ds_historical_mean[var], ds_historical_std[var], 90, 1)
    
    # Calculate fraction as % by multiplying the "better" data-array (1 for better, 0 for other) by the area weight array, then summing over all points.
    
    total_mod = (insig_better + 0).values
    sig_mod = (better + 0).values #returns unweighted numpy array
    insig_mod = total_mod - sig_mod
    
    total_exac = (insig_worse + 0).values
    sig_exac = (worse + 0).values
    insig_exac = total_exac - sig_exac

    return sig_mod, insig_mod, sig_exac, insig_exac


# area_weight uses get_fixed to return the global and land weight of each grid cell. It takes no inputs, since we're only using one model, so all the data is constant.

def area_weight():
    # Use the get_fixed() function to return the gridcell area and land fraction for the model we want.
    ds_area, ds_land = get_fixed('MOHC','UKESM1-0-LL','r1i1p1f2') 
    # NOTE - to do this for another model, you'll need to look up the run number used in the piControl experiment which stores the fx variables.
    # search on CEDA archive for "areacella" and "<MODEL NAME>" and it should show you.

    # Let's define a data array for the area weight of the gridcells
    da_weight = ds_area['areacella'] / ds_area['areacella'].sum()
    da_weight = da_weight.rename(new_name_or_name_dict='area_weight')
    # land area = gricell area * land fraction ([0-100] * 0.01)
    da_land_area = ds_area['areacella'] * ds_land['sftlf'] * 0.01 
    # Now let's create a land area weighting
    da_land_weight = da_land_area / da_land_area.sum()
    
    return da_weight, da_land_weight


# weight takes whatever it is you want weighted and returns the global and land percentage for that thing

def weight(stuff):
    da_weight, da_land_weight = area_weight()
    
    global_weight = 100.*(stuff * da_weight).values.sum()
    land_weight = 100.*(stuff * da_land_weight).values.sum()
    
    return global_weight, land_weight


# climate_change calculates which areas experience significant climate change for that variable. It compares the warming and historical scenarios, then performs a t-test to determine significance at the 95% level

def climate_change(var):
    season,dates,data_dir,model,centre,var,domain,exp,project,runs,grid,time_files = define_parameters(var)
    da_weight, da_land_weight = area_weight()
    num_years = 90

    # Load ssp585 ensemble-mean datasets
    project='ScenarioMIP'
    exp='ssp585'
    dates=['2070-01-01','2100-01-01']
    ds_ssp585_mean, ds_ssp585_std = get_ens_seasonal_mean_std(season, dates, data_dir, model, centre, var, domain, exp, project, runs, grid, time_files=1)# setting time files to zero.

    # Load ssp585 ensemble-mean datasets
    project='CMIP'
    exp='historical'
    dates=['1960-01-01','1990-01-01']
    ds_historical_mean, ds_historical_std = get_ens_seasonal_mean_std(season, dates, data_dir, model, centre, var, domain, exp, project, runs, grid, time_files=1)# setting time files to zero.

    # ttest_sub returns a numpy array of P-values, where P is between 0 and 1. for 95% significance P is below 0.05
    ttest_pvalue = ttest_sub(ds_ssp585_mean[var],ds_ssp585_std[var],num_years,ds_historical_mean[var],ds_historical_std[var],num_years)

    climate_changed_areas = ttest_pvalue < 0.05 #This is a mask
    
    # Calculate fraction as % by multiplying the "better" data-array (1 for better, 0 for other) by the area weight array, then summing over all points.
    global_changed = 100.*((climate_changed_areas) * da_weight).values #.sum() if I want a plain number

    # Calculate fraction as % by multiplying the "better" data-array (1 for better, 0 for other) by the area weight array, then summing over all points.
    land_changed = 100.*((climate_changed_areas) * da_land_weight).values
    #plt.imshow(land_changed) to visualize results
 
    return global_changed, land_changed, climate_changed_areas


# change_mod_exac uses climate_change and mod_exac to calculate which areas experience any combination of changed/unchanged climate and moderation/exacerbation. The outputs of climate_change and mod_exac are numerical arrays, which are combined into arrays depending on each grid value. To get this to work, I have to convert the numerical array output into a boolean array using a mask, and I have to convert it back to a numerical array by adding 0 to each boolean value so it can be weighted. There's probably a more straightforward way to do this, but I haven't figured it out, and this works.

def change_mod_exac(var):
    
    moderated, insig_mod, exacerbated, insig_exac = mod_exac(var)
    global_changed, land_changed, climate_changed_areas = climate_change(var)
    da_weight,da_land_weight = area_weight()
    climate_changed_areas = climate_changed_areas + 0
    #These four lines work fine. They return arrays of 1 and 0

    longitude = len(climate_changed_areas[:,0]) #determining length and width (cell number) of model grid
    latitude = len(climate_changed_areas[0,:])

    changed_moderated = np.empty([longitude,latitude]) #Creating empty numpy arrays the size of the grid
    changed_exacerbated = np.empty([longitude,latitude])
    unchanged_moderated = np.empty([longitude,latitude])
    unchanged_exacerbated = np.empty([longitude,latitude])

    for i in range(0, longitude-1):
        for j in range(0, latitude-1):
            if climate_changed_areas[i,j] == 1: #Finding areas that experience significant climate change
                unchanged_moderated[i,j] = 0
                unchanged_exacerbated[i,j] = 0
                if moderated[i,j] == 1:         #Finding moderated areas w/ sig climate change
                    changed_moderated[i,j] = 1
                    changed_exacerbated[i,j] = 0
                elif exacerbated[i,j] == 1:     #Finding exacerbated areas w/ sig climate change
                    changed_moderated[i,j] = 0
                    changed_exacerbated[i,j] = 1
                
            else:                              #Areas that don't experience significant climate change
                changed_moderated[i,j] = 0
                changed_exacerbated[i,j] = 0
                if moderated[i,j] == 1:         #Finding moderated areas w/out sig climate change
                    changed_moderated[i,j] = 1
                    changed_exacerbated[i,j] = 0
                elif exacerbated[i,j] == 1:     #Finding exacerbated areas w/out sig climate change
                    changed_moderated[i,j] = 0
                    changed_exacerbated[i,j] = 1
                    
    #c=changed,u=unchanged                  the names were just getting a bit long
    #m=moderated,e=exacerbated
    #g=global,l=land    
    
    cm = changed_moderated == 1
    um = unchanged_moderated == 1
    ce = changed_exacerbated == 1
    ue = unchanged_exacerbated == 1
    #These four lines apply a mask, which only takes the values where both were == 1 in the loop above.
    #Both true = 1, so it returns a boolean array
    #This solves the problem I had where the 0s in the array were becoming other numbers.
    #I have to convert back to numerical data below, so I can use area weighting.

    cmg = 100*((cm+0)*da_weight).values.sum()
    ceg = 100*((ce+0)*da_weight).values.sum()
    cml = 100*((cm+0)*da_land_weight).values.sum()
    cel = 100*((ce+0)*da_land_weight).values.sum()

    umg = 100*((um+0)*da_weight).values.sum()
    ueg = 100*((ue+0)*da_weight).values.sum()
    uml = 100*((um+0)*da_land_weight).values.sum()
    uel = 100*((ue+0)*da_land_weight).values.sum()
    
    return cmg,ceg,cml,cel,umg,ueg,uml,uel


# global_mean returns a numerical value representing the global mean of that variable over that time period

def global_mean(var,exp,dates,project):
    season,dates1,data_dir,model,centre,var1,domain,exp1,project1,runs,grid,time_files = define_parameters(var)
    
    # Use the get_fixed() function to return the gridcell area and land fraction for the model we want.
    ds_area, ds_land = get_fixed('MOHC','UKESM1-0-LL','r1i1p1f2') 

    # Let's define a data array for the area weight of the gridcells
    da_weight = ds_area['areacella'] / ds_area['areacella'].sum()
    da_weight = da_weight.rename(new_name_or_name_dict='area_weight')

    # load the arguments into a list then... 
    args=[season,dates,data_dir,model,centre,var,domain,exp,project,runs,grid,time_files]
    ds_mean, ds_std = get_ens_seasonal_mean_std(*args) # ... unpack them into the function.
    
    # multiply each temperature value with its corresponding fraction of total area, then sum to find the global mean.
    return (ds_mean[var]*da_weight).sum()