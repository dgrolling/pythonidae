# -*- coding: utf-8 -*-
"""
Created on Thu Jul  8 13:59:37 2021

@author: DGrolling
"""

import os
import arcpy as ap
import numpy as np
import pandas as pd
import re
pd.options.mode.chained_assignment = None

from datetime import datetime as dt
start_time = dt.now()


# crete variables for file creation
work_path       = r"C:\\PSU\\Final Project\\Data\\"
raw_input       = work_path + "NPI2021_TestSet.csv"
for_geo         = work_path + "Working\\NPI2021_ForGeocoding.csv"
final_path      = work_path + "Final\\NPI2021_GeocodedFinal.csv"
geocoded        = work_path + "Working\\NPIProcessing_GeocodedFIPS.csv"
geocoded_xml    = work_path + "Working\\NPIProcessing_GeocodedFIPS.csv.xml"
state_sum       = work_path + "Final\\NPI2021_StateSummary.csv"
county_sum      = work_path + "Final\\NPI2021_CountySummary.csv"
state_pop       = work_path + "StatePopulation.csv"
county_pop      = work_path + "CountyPopulation.csv"

ap.env.workspace = "C:\\PSU\\Final Project\\Data\\NPIProcessing.gdb"
ap.env.overwrite = True

# read raw data in and sort
df = pd.read_csv(raw_input, nrows=1000, na_filter=False, low_memory=False, dtype={'NPI' : str})
df.sort_values(by=['NPI'])

# print column names
# print(df.head(0))
# for c in df.head(0):
#     print(c)

# local variable creation
df['GeoStreet']   = ""
df['GeoCity']     = ""
df['GeoState']    = ""
df['GeoZipFive']  = ""

# take subset of data frame for only NPI individuals and fields needed for geocoding
df2 = df[['NPI', 
          'Entity Type Code', 
          'Provider First Line Business Mailing Address', 
          'Provider Second Line Business Mailing Address',
          'Provider Business Mailing Address City Name', 
          'Provider Business Mailing Address State Name',
          'Provider Business Mailing Address Postal Code', 
          'Provider First Line Business Practice Location Address',
          'Provider Second Line Business Practice Location Address', 
          'Provider Business Practice Location Address City Name',
          'Provider Business Practice Location Address State Name', 
          'Provider Business Practice Location Address Postal Code',
          'GeoStreet',
          'GeoCity',
          'GeoState',
          'GeoZipFive']]


# set up algorithm to create preferred provider address for geocoding

'''
if first line business practice address contains 'PO BOX' and
first line business mailing address contains 'PO BOX' then
'Provider_Prefer_Add_Street' == first line business mailing address
else it == first line business practice address
'''    
mail_street     = df2['Provider First Line Business Mailing Address']
practice_street = df2['Provider First Line Business Practice Location Address']

df2['GeoStreet'] = np.where((mail_street.str.contains('PO BOX')) & (practice_street.str.contains('PO BOX')), mail_street, practice_street)


'''
if first line business practice address contains 'PO BOX' and
first line business mailing address contains 'PO BOX' then
'Provider_Prefer_Add_City' == business mailing city
else it == business practice city
'''
mail_city       = df2['Provider Business Mailing Address City Name']
practice_city   = df2['Provider Business Practice Location Address City Name']
       
df2['GeoCity'] = np.where((mail_street.str.contains('PO BOX')) & (practice_street.str.contains('PO BOX')), mail_city, practice_city)

'''
if first line business practice address contains 'PO BOX' and
first line business mailing address contains 'PO BOX' then
'Provider_Prefer_Add_City' == business mailing state
else it == business practice state
'''
mail_state      = df2['Provider Business Mailing Address State Name']
practice_state  = df2['Provider Business Practice Location Address State Name']

df2['GeoState'] = np.where((mail_street.str.contains('PO BOX')) & (practice_street.str.contains('PO BOX')), mail_state, practice_state)

'''
if first line business practice address contains 'PO BOX' and
first line business mailing address contains 'PO BOX' then
'Provider_Prefer_Add_City' == business mailing zip
else it == business practice zip
'''
mail_zip        = df2['Provider Business Mailing Address Postal Code']
practice_zip    = df2['Provider Business Practice Location Address Postal Code']

df2['GeoZipFive'] = np.where((mail_street.str.contains('PO BOX')) & (practice_street.str.contains('PO BOX')), mail_zip, practice_zip)

# export data frame to CSV for importing into ArcGIS Pro
df3 = df2[(df2['GeoStreet']!="") & (df2['GeoState']!="")]

print("---------------------")
print("|  FILE PROCESSING  |")
print("---------------------")
print("There are {} of {} records with a complete address which will be used for processing".format(len(df3),len(df2)))
print("---------------------")

df4 = df3[['NPI','GeoStreet','GeoCity','GeoState','GeoZipFive']]

if os.path.exists(for_geo):
  os.remove(for_geo)

df4.to_csv(for_geo, index=False)

# handle situations where the data already exists
fileexists = ["NPI2021_ForGeocoding", "NPIProcessing_Geocoded", "NPIProcessing_GeocodedFIPS", 
              "NPIProcessing_BG", "NPIProcessing_BG_HPSA", "NPIProcessing_BG_HPSA_MUAP"]

for f in fileexists:
    if ap.Exists(f):
        ap.Delete_management(f)
    
# read CSV file into GDB as a table
ap.conversion.TableToTable(for_geo, ap.env.workspace, "NPI2021_ForGeocoding")
print("File with {} records imported to GDB".format(len(df4)))
print("---------------------")

# execute geocoding on GDB table
ap.GeocodeAddresses_geocoding(in_table="NPI2021_ForGeocoding", 
                              address_locator="L:/HealthLandscape/StreetmapPremium2020R4/ClassicLocators/USA_ZIP4_LocalComposite", 
                              in_address_fields="Address GeoStreet VISIBLE NONE;City GeoCity VISIBLE NONE;State GeoState VISIBLE NONE;ZIP_Code GeoZipFive VISIBLE NONE;ZIP4 <None> VISIBLE NONE", 
                              out_feature_class=ap.env.workspace + "/NPIProcessing_Geocoded", 
                              out_relationship_type="STATIC", 
                              country="", 
                              location_type="ROUTING_LOCATION")
print("Address records have been geocoded")
print("---------------------")

# execute spatial join(s) on geocoded file
# block groups
ap.analysis.SpatialJoin(ap.env.workspace + "/NPIProcessing_Geocoded",
                        ap.env.workspace + "/BlockGroups_2010",
                        ap.env.workspace + "/NPIProcessing_BG",
                        "JOIN_ONE_TO_ONE",
                        "KEEP_ALL",
                        'X "X" true true false 8 Double 0 0,First,#,test,X,-1,-1;Y "Y" true true false 8 Double 0 0,First,#,test,Y,-1,-1;USER_GeoStreet "GeoStreet" true true false 255 Text 0 0,First,#,test,USER_GeoStreet,0,255;USER_GeoCity "GeoCity" true true false 255 Text 0 0,First,#,test,USER_GeoCity,0,255;USER_GeoState "GeoState" true true false 255 Text 0 0,First,#,test,USER_GeoState,0,255;USER_GeoZipFive "GeoZipFive" true true false 255 Text 0 0,First,#,test,USER_GeoZipFive,0,255;USER_NPI "NPI" true true false 255 Text 0 0,First,#,test,USER_NPI,0,255;USER_usegeo "usegeo" true true false 255 Text 0 0,First,#,test,USER_usegeo,0,255;STATE_FIPS "STATE_FIPS" true true false 2 Text 0 0,First,#,Block_Groups_Spatial_Join,STATE_FIPS,0,2;CNTY_FIPS "CNTY_FIPS" true true false 3 Text 0 0,First,#,Block_Groups_Spatial_Join,CNTY_FIPS,0,3;STCOFIPS "STCOFIPS" true true false 5 Text 0 0,First,#,Block_Groups_Spatial_Join,STCOFIPS,0,5;TRACT "TRACT" true true false 6 Text 0 0,First,#,Block_Groups_Spatial_Join,TRACT,0,6;BLKGRP "BLKGRP" true true false 1 Text 0 0,First,#,Block_Groups_Spatial_Join,BLKGRP,0,1;FIPS "FIPS" true true false 12 Text 0 0,First,#,Block_Groups_Spatial_Join,FIPS,0,12;Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,Block_Groups_Spatial_Join,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0,First,#,Block_Groups_Spatial_Join,Shape_Area,-1,-1', "INTERSECT", None, None)

# primary care HPSAs
ap.analysis.SpatialJoin(ap.env.workspace + "/NPIProcessing_BG",
                        ap.env.workspace + "/PCHPSA_2020",
                        ap.env.workspace + "/NPIProcessing_BG_HPSA",
                        "JOIN_ONE_TO_ONE",
                        "KEEP_ALL",
                        'X "X" true true false 8 Double 0 0,First,#,test,X,-1,-1;Y "Y" true true false 8 Double 0 0,First,#,test,Y,-1,-1;USER_GeoStreet "GeoStreet" true true false 255 Text 0 0,First,#,test,USER_GeoStreet,0,255;USER_GeoCity "GeoCity" true true false 255 Text 0 0,First,#,test,USER_GeoCity,0,255;USER_GeoState "GeoState" true true false 255 Text 0 0,First,#,test,USER_GeoState,0,255;USER_GeoZipFive "GeoZipFive" true true false 255 Text 0 0,First,#,test,USER_GeoZipFive,0,255;USER_NPI "NPI" true true false 255 Text 0 0,First,#,test,USER_NPI,0,255;USER_usegeo "usegeo" true true false 255 Text 0 0,First,#,test,USER_usegeo,0,255;STATE_FIPS "STATE_FIPS" true true false 2 Text 0 0,First,#,Block_Groups_Spatial_Join,STATE_FIPS,0,2;CNTY_FIPS "CNTY_FIPS" true true false 3 Text 0 0,First,#,Block_Groups_Spatial_Join,CNTY_FIPS,0,3;STCOFIPS "STCOFIPS" true true false 5 Text 0 0,First,#,Block_Groups_Spatial_Join,STCOFIPS,0,5;TRACT "TRACT" true true false 6 Text 0 0,First,#,Block_Groups_Spatial_Join,TRACT,0,6;BLKGRP "BLKGRP" true true false 1 Text 0 0,First,#,Block_Groups_Spatial_Join,BLKGRP,0,1;FIPS "FIPS" true true false 12 Text 0 0,First,#,Block_Groups_Spatial_Join,FIPS,0,12;HpsSrcID "HpsSrcID" true true false 12 Text 0 0,First,#,Block_Groups_Spatial_Join,HpsSrcID,0,12;Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,Block_Groups_Spatial_Join,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0,First,#,Block_Groups_Spatial_Join,Shape_Area,-1,-1', "INTERSECT", None, None)

# MUAPs
ap.analysis.SpatialJoin(ap.env.workspace + "/NPIProcessing_BG_HPSA",
                        ap.env.workspace + "/MUAP_2020",
                        ap.env.workspace + "/NPIProcessing_BG_HPSA_MUAP",
                        "JOIN_ONE_TO_ONE",
                        "KEEP_ALL",
                        'X "X" true true false 8 Double 0 0,First,#,test,X,-1,-1;Y "Y" true true false 8 Double 0 0,First,#,test,Y,-1,-1;USER_GeoStreet "GeoStreet" true true false 255 Text 0 0,First,#,test,USER_GeoStreet,0,255;USER_GeoCity "GeoCity" true true false 255 Text 0 0,First,#,test,USER_GeoCity,0,255;USER_GeoState "GeoState" true true false 255 Text 0 0,First,#,test,USER_GeoState,0,255;USER_GeoZipFive "GeoZipFive" true true false 255 Text 0 0,First,#,test,USER_GeoZipFive,0,255;USER_NPI "NPI" true true false 255 Text 0 0,First,#,test,USER_NPI,0,255;USER_usegeo "usegeo" true true false 255 Text 0 0,First,#,test,USER_usegeo,0,255;STATE_FIPS "STATE_FIPS" true true false 2 Text 0 0,First,#,Block_Groups_Spatial_Join,STATE_FIPS,0,2;CNTY_FIPS "CNTY_FIPS" true true false 3 Text 0 0,First,#,Block_Groups_Spatial_Join,CNTY_FIPS,0,3;STCOFIPS "STCOFIPS" true true false 5 Text 0 0,First,#,Block_Groups_Spatial_Join,STCOFIPS,0,5;TRACT "TRACT" true true false 6 Text 0 0,First,#,Block_Groups_Spatial_Join,TRACT,0,6;BLKGRP "BLKGRP" true true false 1 Text 0 0,First,#,Block_Groups_Spatial_Join,BLKGRP,0,1;FIPS "FIPS" true true false 12 Text 0 0,First,#,Block_Groups_Spatial_Join,FIPS,0,12;HpsSrcID "HpsSrcID" true true false 12 Text 0 0,First,#,Block_Groups_Spatial_Join,HpsSrcID,0,12;MuaSrcID "MuaSrcID" true true false 12 Text 0 0,First,#,Block_Groups_Spatial_Join,MuaSrcID,0,12;Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,Block_Groups_Spatial_Join,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0,First,#,Block_Groups_Spatial_Join,Shape_Area,-1,-1', "INTERSECT", None, None)

print("Geocoded file has been enriched with PC HPSA, MUAP, and Census FIPS codes")
        
# export spatially-enriched and geocoded feature class to CSV for post-processing
if os.path.exists(geocoded):
  os.remove(geocoded)
  
if os.path.exists(geocoded_xml):
  os.remove(geocoded_xml)

ap.TableToTable_conversion(ap.env.workspace + "/NPIProcessing_BG_HPSA_MUAP", 
                              out_path="C:/PSU/Final Project/Data/Working", 
                              out_name="NPIProcessing_GeocodedFIPS.csv", 
                              where_clause="", 
                              field_mapping='Join_Count "Join_Count" true true false 4 Long 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,Join_Count,-1,-1;TARGET_FID "TARGET_FID" true true false 4 Long 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,TARGET_FID,-1,-1;X "X" true true false 8 Double 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,X,-1,-1;Y "Y" true true false 8 Double 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,Y,-1,-1;USER_GeoSt "GeoStreet" true true false 255 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,USER_GeoStreet,-1,-1;USER_GeoCi "GeoCity" true true false 255 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,USER_GeoCity,-1,-1;USER_Geo_1 "GeoState" true true false 255 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,USER_GeoState,-1,-1;USER_GeoZi "GeoZipFive" true true false 255 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,USER_GeoZipFive,-1,-1;USER_NPI "NPI" true true false 255 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,USER_NPI,-1,-1;USER_usege "usegeo" true true false 255 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,USER_usegeo,-1,-1;STATE_FIPS "STATE_FIPS" true true false 2 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,STATE_FIPS,-1,-1;CNTY_FIPS "CNTY_FIPS" true true false 3 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,CNTY_FIPS,-1,-1;STCOFIPS "STCOFIPS" true true false 5 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,STCOFIPS,-1,-1;TRACT "TRACT" true true false 6 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,TRACT,-1,-1;BLKGRP "BLKGRP" true true false 1 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,BLKGRP,-1,-1;FIPS "FIPS" true true false 12 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,FIPS,-1,-1;HpsSrcID "HpsSrcID" true true false 12 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,HpsSrcID,-1,-1;MuaSrcID "MuaSrcID" true true false 12 Text 0 0 ,First,#,NPIProcessing_BG_HPSA_MUAP,MuaSrcID,-1,-1', 
                              config_keyword="")
print("Processed file exported as CSV")

# read in and define fields as text to retain leading zeroes
dfgeo = pd.read_csv(geocoded, nrows=10000, na_filter=False, low_memory=False, dtype={'USER_NPI' : str,
                                                                                    'STCOFIPS': str, 
                                                                                    'FIPS' : str,
                                                                                    'STATE_FIPS' : str,
                                                                                    'CNTY_FIPS' : str,
                                                                                    'TRACT' : str,
                                                                                    'BLKGRP' : str,
                                                                                    'HpsSrcID' : str,
                                                                                    'MuaSrcID' : str})


# merge with raw data and export to final file
dfgeo.sort_values(by=['USER_NPI'])
npi_geo = pd.merge(left=df, right=dfgeo, left_on='NPI', right_on='USER_NPI', how='left')


# create indicator for primary care physicians
prim_care_phys = ['207Q00000X','207QA0401X','207QA0000X','207QA0505X','207QB0002X','207QG0300X', 
                  '207QH0002X','207QS1201X','207QS0010X','208D00000X','207R00000X','207RA0000X',
                  '207RG0300X','208000000X','2080A0000X']
npi_geo['PCP_IND'] = [1 if x in prim_care_phys else 0 for x in npi_geo['Healthcare Provider Taxonomy Code_1']]


# create indicator for nurse practitioners
nurse_pract  = ['363L00000X','363LA2100X','363LA2200X','363LC0200X','363LC1500X','363LF0000X',
                '363LG0600X','363LN0000X','363LN0005X','363LP0200X','363LP0222X','363LP0808X',
                '363LP1700X','363LP2300X','363LS0200X','363LW0102X','363LX0001X','363LX0106X']
npi_geo['NP_IND'] = [1 if x in nurse_pract  else 0 for x in npi_geo['Healthcare Provider Taxonomy Code_1']]


# create indicator for midwives
mwife_pract  = ['176B00000X','367A00000X','175M00000X']
npi_geo['MWIFE_IND'] = [1 if x in mwife_pract  else 0 for x in npi_geo['Healthcare Provider Taxonomy Code_1']]

# create indicator for physician assistants
phys_assist   = ['363A00000X','363AM0700X','363AS0400X']
npi_geo['PA_IND'] = [1 if x in phys_assist   else 0 for x in npi_geo['Healthcare Provider Taxonomy Code_1']]


# create indicator for all providers in primary care
pc_list = ['207Q00000X','207QA0401X','207QA0000X','207QA0505X','207QB0002X','207QG0300X', 
           '207QH0002X','207QS1201X','207QS0010X','208D00000X','207R00000X','207RA0000X',
           '207RG0300X','208000000X','2080A0000X','363L00000X','363LA2100X','363LA2200X',
           '363LC0200X','363LC1500X','363LF0000X','363LG0600X','363LN0000X','363LN0005X',
           '363LP0200X','363LP0222X','363LP0808X','363LP1700X','363LP2300X','363LS0200X',
           '363LW0102X','363LX0001X','363LX0106X']
npi_geo['PC_IND'] = [1 if x in pc_list else 0 for x in npi_geo['Healthcare Provider Taxonomy Code_1']]


# create indicator for family physicians using regex
fp_pattern = re.compile('207Q.+')
fp_matches = [string for string in npi_geo['Healthcare Provider Taxonomy Code_1'] if re.match(fp_pattern, string)]
npi_geo['FP_IND'] = [1 if x in fp_matches else 0 for x in npi_geo['Healthcare Provider Taxonomy Code_1']]


# create indicator for primary care HPSA
npi_geo['PCHPSA_IND'] = [1 if x != "" else 0 for x in npi_geo['HpsSrcID']]


# create indicator for MUAP
npi_geo['MUAP_IND'] = [1 if x != "" else 0 for x in npi_geo['MuaSrcID']]


# create indicator for whether provider is in either a PC HPSA or MUAP
npi_geo['HPSA_MUAP_IND'] = [1 if x == 1 or y == 1 else 0 for (x,y) in zip(npi_geo['PCHPSA_IND'],npi_geo['MUAP_IND'])]


# final file creation
if os.path.exists(final_path):
  os.remove(final_path)

npi_geo.to_csv(final_path, index=False)

# create summary measures for printing
pct_hpsa = round((npi_geo['PCHPSA_IND'].sum() / len(npi_geo['PCHPSA_IND']) * 100),1)
pct_muap = round((npi_geo['MUAP_IND'].sum() / len(npi_geo['MUAP_IND']) * 100),1)
pct_hpsa_muap = round((npi_geo['HPSA_MUAP_IND'].sum() / len(npi_geo['HPSA_MUAP_IND']) * 100),1)
pct_pa  = round((npi_geo['PA_IND'].sum() / len(npi_geo['PA_IND']) * 100),1)
pct_np  = round((npi_geo['NP_IND'].sum() / len(npi_geo['NP_IND']) * 100),1)
pct_pcp = round((npi_geo['PCP_IND'].sum() / len(npi_geo['PCP_IND']) * 100),1)
pct_fp  = round((npi_geo['FP_IND'].sum() / len(npi_geo['FP_IND']) * 100),1)
pct_pc  = round((npi_geo['PC_IND'].sum() / len(npi_geo['PC_IND']) * 100),1)
pct_mw  = round((npi_geo['MWIFE_IND'].sum() / len(npi_geo['MWIFE_IND']) * 100),1)

print("---------------------")
print("|SUMMARY INFORMATION|")
print("---------------------")
print("{} ({}%) of all NPI providers practice in a PC HPSA".format(npi_geo['PCHPSA_IND'].sum(), pct_hpsa))
print("{} ({}%) of all NPI providers practice in a MUAP".format(npi_geo['MUAP_IND'].sum(), pct_muap))
print("{} ({}%) of all NPI providers practice in a PC HPSA or a MUAP".format(npi_geo['HPSA_MUAP_IND'].sum(), pct_hpsa_muap))
print("---------------------")
print("There are {} ({}%) physician assistants".format(npi_geo['PA_IND'].sum(), pct_pa))
print("There are {} ({}%) nurse practitioners".format(npi_geo['NP_IND'].sum(), pct_np))
print("There are {} ({}%) primary care physicians".format(npi_geo['PCP_IND'].sum(), pct_pcp))
print("There are {} ({}%) family physicians".format(npi_geo['FP_IND'].sum(), pct_fp))
print("There are {} ({}%) providers in primary care".format(npi_geo['PC_IND'].sum(), pct_pc))
print("There are {} ({}%) mid-wives".format(npi_geo['MWIFE_IND'].sum(), pct_mw))
print("---------------------")

# create state-level summry file for all specialties and geographic indicators
npi_st_stat = npi_geo[["STATE_FIPS", "PA_IND", "NP_IND", "PCP_IND", "FP_IND", "PC_IND", "MWIFE_IND", "PCHPSA_IND", "MUAP_IND", "HPSA_MUAP_IND"]]
npi_st_sum = npi_st_stat.groupby("STATE_FIPS").sum().reset_index()
npi_st_sum.sort_values(by=["STATE_FIPS"])

stpop = pd.read_csv(state_pop, dtype={'STATE' : str})
stpop.sort_values(by=["STATE"])   
state_pop_sum = pd.merge(left=npi_st_sum, right=stpop, left_on='STATE_FIPS', right_on='STATE', how='left')
state_pop_sum.to_csv(state_sum, index=False)

# create county-level summry file for all specialties and geographic indicators
npi_c_stat = npi_geo[["STCOFIPS", "PA_IND", "NP_IND", "PCP_IND", "FP_IND", "PC_IND", "MWIFE_IND", "PCHPSA_IND", "MUAP_IND", "HPSA_MUAP_IND"]]
npi_c_sum = npi_c_stat.groupby("STCOFIPS").sum().reset_index()
npi_c_sum.sort_values(by=["STCOFIPS"])

cpop = pd.read_csv(county_pop, dtype={'STCOFIPS' : str})
cpop.sort_values(by=["STCOFIPS"])   
c_pop_sum = pd.merge(left=npi_c_sum, right=cpop, left_on='STCOFIPS', right_on='STCOFIPS', how='left')
c_pop_sum.to_csv(county_sum, index=False)

print("Processing finished...state and county-level summary files have been exported")
end_time = dt.now()
print('Duration: {}'.format(end_time - start_time))


