# geoengineering_summer
quigley_general_table.ipynb is likely to be the final iteration of the table. It's not fully working yet, but it's the general version of the table that can accept a list of variables and output a csv file with the data analysed by metric.
quigley_table_rough.ipynb is a working table, but it currently uses a short list of variables that we already have the data for (and work with Amon). quigley_general_table.ipynb started with this code, but I created the variable list from the spreadsheet (now csv) that we worked on. I set 'var' as the index of this table, so it searches for domain and project based on each variable. This, in theory, ensures compatibility.
All the other ipynb files are things that didn't quite pan out, but I like to keep all my code, at least until I have a finished project.
CMIP_variables.csv is the file that creates var_list and is used to determine which domain and project correspond to which variable. It's the input.
metric_table.csv is the output of quigley_table_rough.ipynb
