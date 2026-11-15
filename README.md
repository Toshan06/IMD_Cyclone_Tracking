# TRACK of IMD Cyclones
### IMD Best Track of Cyclones from 1982 to 2025

Group members:  Toshan, Ganesh, Suhash, Armaan

## OVERVIEW & PURPOSE
The aim of this project is to create a visualization for the cyclone trajectories obtained from the IMD (Indian Meteorological Department) dataset starting from 1982 to 2025 across the three basins of origin i.e. Arabian Sea (AS), Bay of Bengal (BOB), Land (LAND).

## DATASETS & SOFTWARE USED
- IMD_Best_Tracks_Data_1982-2025 Data used
- Jupyter Notebook & Python3.15 environment
- Streamlit web app platform

## METHODOLOGY
- Obtain the IMD Dataset.
- Clean / Pre-process the dataset: Retain only those columns that would be useful for data analysis: Serial Number of system during year, Basin of origin, Name, Date (DD-MM-YYYY), Time (UTC), Latitude (lat.), Longitude (lon.), CI No [or "T. No"], Maximum Sustained Surface Wind (kt), Pressure Drop (hPa) [or "delta P"], Grade (text)
- Plot each Cyclone track using Matplotlib & Cartopy.
- Make an interactive visualization using Streamlit, where the user can vary the Year, Basin of Origin and Cyclone name according to their requirement to get the geographical trajectory, T number ~ Date, Maximum Sustained Surface Wind speed ~ Date & Pressure Drop ~ Date for each cyclone or all of them together. (The link to the codebase is provided below.)

## RESULTS
An interactive Geographical map of the trajectories of Cyclones that has hit the Indian subcontinent from 1982 to 2025 made using Python.
