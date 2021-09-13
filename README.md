# pythonidae

### Introduction
This is a stand alone Python solution to geoprocess and create analyses for the Centers for Medicare and Medicaid National Provider Identifier file (NPI). 

### Purpose
This project was aimed at taking an existing workflow that I employ in my job and replace it with a streamlined approach using Python programming. The current workflow consists of using SAS programming to pre-process a raw dataset containing public records on licensed healthcare professionals, geocode and enrich them using ArcGIS Pro, then perform post-processing with SAS software to create a final dataset. This process is a multi-application, multi-format, semi-manual approach that is prone to issues that compromise data integrity each time the raw set is processed. Creating a single-application, single automated workflow using a single Python script was a necessary alternative.

### Development
I’m responsible for processing these data each quarter and since the SAS code used in pre- and post-processing doesn’t change from file to file other than input and output naming conventions, the logic of the workflow already existed. The first task was to review the SAS logic to see where I could translate the syntax from SAS to Python.  Overall, I kept the Python logic in similar structure having the preprocessing steps at the beginning. These steps are needed to create a set of preferred address fields for each provider since each one has two addresses. Once those were created, I reduced my data frame from over 300 fields to 5 to do the geocoding and enriching. This step utilized the arcpy package to take the exported pandas data frame as a CSV and import it into a file geodatabase. Next, the table is geocoded then enriched with three different polygon feature classes to append GEOIDs from each one.

The enriched file is exported out as a CSV file and read back in as a pandas data frame. Lastly, this data frame is merged back with the raw data frame. In the final file prep stage, indicators are created based on taxonomy codes that describes the type of specialist the provider is; a family physician or a nurse practitioner, for example. Several more indicators are also created based on the enriched GEOIDs to denote which geography types (Census blocks, medically underserved areas, or health professional shortage areas) each provider falls into based on the geocoded address.

Before a final processed file is exported, several print statements are executed to produce a kind of report. This report details the number of providers that were geocoded to positions inside of the three levels of geography, and the number and percentage of certain types of providers like family physicians, physician assistants, or whether they work in primary care.

Because I had time left over at the end, there are two blocks of statements at the end of the program that creates an aggregated state- and county-level set of files where each one contains a summation of the number of provider specialties by their respective geography file (state or county). These files will be used as reporting files when clients quickly want to know answers to questions like “How many primary care physicians are practicing in Iowa?”.

### Lessons Learned
What I learned most was about code management. Organizing code and clearing up redundancies was one of my overall aims in taking this course and even though my final project code is redundant in places, I do feel more organized and clear-headed when working with code. Writing a multi-step processing script like my final project needs code documentation to explain what all the steps are doing and I’ve learned to use that to refer back to what I was thinking when working out the logic.

I also discovered through this project that you don’t always need a robust statistical software solution like SAS to do this kind of processing. Python can handle large complex data; something I wasn’t sure about before.

One other thing I learned was that with a course project like this, I had much more creative freedom than if it was a project for a customer at work. I spent more time than needed ‘playing’ around with code functionality, print statements, and processing enhancements, but it led me to explore what I can add to the work-related processing in the future.

### Evaluation Steps
1.	Hard coded paths to input and output data files need to be updated in lines 20-29. I’d suggest retaining the file names. The main directory is in line 20 and lines 21-29 refer to files that are separated into subfolders to manage the working and final files better.
2.	Local workspace in line 31 also needs to be updated
3.	The geocoding locator file used on line 145 is local to my work’s virtual machine and will need to be swapped out. I used the StreetMap Premium UDS_ZIP4_LocalComposite locator file.
4.	Hard coded path on line 189 needs to be updated
5.	Once items 1-4 are remedied, then the script can be run.
6.	Program success will be measured by the creation of three files in the Final folder: “NPI2021_CountySummary.csv”, “NPI2021_StateSummary.csv”, and “NPI2021_GeocodedFinal.csv”

### Processing Notes
•	There are two CSV files, “CountyPopulation.csv” and “StatePopulation.csv” in the Data folder that are appended to a data frame at the end of the script. These files contain state- and county-level population and will be used to calculate statistics (not a part of final project).
•	In the report statements printed to the console, there is a statement “There are 0 (0.0%) mid-wives”. This specialty type doesn’t occur frequently so there are truly none in the sample set.

![alt text](https://static.thenounproject.com/png/1390001-200.png)
