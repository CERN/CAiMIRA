import pandas as pd
from tabulate import tabulate

'''
Script file to generate the vaccine effectiveness values.
To generate the primary vaccine effectiveness values, uncomment lines 16-21.
To generate the booster effectiveness values, uncomment lines 26-56.
'''

# Data from 08 Sep. 2022
file_loc = "https://caimira-resources.web.cern.ch/WeeklySummary_COVID19_VE_Studies_08Sep2022_adapted.xlsx"


# ------- PRIMARY VACCINATION ------ #

# df = pd.read_excel(file_loc, sheet_name="Primary_filtered", usecols="A, B, E")

# calculate the VE value
# df = df.drop(df[df['VE'] < 0].index)
# ve_data = df.groupby(['vaccine'])['VE'].mean().divide(100).reset_index()
# print(tabulate(ve_data, headers='keys', tablefmt='psql'))


# ------- BOOSTER VACCINATION ------ #

# df = pd.read_excel(file_loc, sheet_name="Booster_filtered", usecols="A, B, C, F")

# # create df without the '  or  ' substring in primary vaccines
# rows_with_or = df[df['primary series vaccine'].str.contains(' or ')]
# rows_indexes = list(rows_with_or.index)
# df_without_or = df.drop(labels=rows_indexes, axis=0)

# # copy of all the rows that contain '  or  '
# new_rows_with_or = rows_with_or.reset_index().copy()

# # create new dataframe empty
# rows_to_add = pd.DataFrame(columns=rows_with_or.columns)

# # duplicate each row and add it into the new dataframe
# for index, row in new_rows_with_or.iterrows():
#     new_rows_with_or.at[index, 'primary series vaccine'] = row['primary series vaccine'].split(' or ')[0]
#     rows_to_add.loc[index] = new_rows_with_or.loc[index]
#     new_rows_with_or.at[index, 'primary series vaccine'] = row['primary series vaccine'].split(' or ')[1]
#     rows_to_add.loc[len(rows_indexes)+index] = new_rows_with_or.loc[index]

# # merge the dataframe without the '  or  ' with the new dataframe that has the rows divided in two
# final_df = pd.concat([df_without_or, rows_to_add]).reset_index().drop(columns=['index'])

# # calculate the VE value
# final_df = final_df.drop(final_df[final_df['VE'] < 0].index)

# ve_data = final_df.groupby(['primary series vaccine', 'booster vaccine'])['VE'].mean().divide(100).reset_index()

# result = ve_data.to_dict('records')

# print(tabulate(ve_data, headers='keys', tablefmt='psql'))
