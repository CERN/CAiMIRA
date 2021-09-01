from cara.model_scenarios import exposure_model_from_vl_breathing, exposure_model_from_vl_talking, exposure_model_from_vl_talking_cn, exposure_model_from_vl_talking_new_points
import numpy as np
import csv

viral_loads = np.linspace(2, 12, 600)

#er_means = exposure_model_from_vl_talking(viral_loads)
#er_means = exposure_model_from_vl_talking_new_points(viral_loads)
#er_means = exposure_model_from_vl_breathing(viral_loads)
#er_means = exposure_model_from_vl_talking_cn(viral_loads)

# with open('data.csv', 'w', newline='') as csvfile:
#     fieldnames = ['viral load', 'emission rate']
#     thewriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
#     thewriter.writeheader()
#     for i, vl in enumerate(viral_loads):
#         thewriter.writerow(
#             {'viral load': 10**vl, 'emission rate': er_means[i]})


def fit_function_to_data_points():

    rna_copies = np.array([4.01624,
                  4.38393,
                  4.65486,
                  4.99213,
                  5.35982,
                  5.66392,
                  5.90444,
                  6.11178,
                  6.30254,
                  6.47947,
                  6.67023,
                  6.83057,
                  6.97433,
                  7.13467,
                  7.24802,
                  7.4056,
                  7.59912,
                  7.80646,
                  7.9834,
                  8.11057,
                  8.23774,
                  8.41467,
                  8.55843,
                  8.74918,
                  8.97311,
                  9.23022,
                  9.43756,
                  9.74166,
                  10.06235,
                  10.34987,
                  10.59038,
                  10.76455,
                  10.92489])

    r_inf = np.array([0.004036804,
             0.003189439,
             0.003189439,
             0.007288068,
             0.013790595,
             0.022835218,
             0.03258901,
             0.043190166,
             0.05392952,
             0.066083573,
             0.080077827,
             0.093079245,
             0.108626396,
             0.121773284,
             0.135622068,
             0.149616322,
             0.171666,
             0.192864676,
             0.212510456,
             0.228057606,
             0.238658763,
             0.254205913,
             0.268905699,
             0.284452849,
             0.3,
             0.315547151,
             0.326995672,
             0.338444194,
             0.346641452,
             0.353143979,
             0.356391606,
             0.357242608,
             0.357242608])

    result = np.polyfit(rna_copies, r_inf, 1)
    print(result)

fit_function_to_data_points()
