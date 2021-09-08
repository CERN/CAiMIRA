import numpy as np

import cara.monte_carlo as mc
from cara.monte_carlo.sampleable import Normal,LogNormal,LogCustomKernel, Uniform


# From CERN-OPEN-2021-04 and refererences therein
activity_distributions = {
    'Seated': mc.Activity(LogNormal(-0.6872121723362303, 0.10498338229297108),
                          LogNormal(-0.6872121723362303, 0.10498338229297108)),

    'Standing': mc.Activity(LogNormal(-0.5742377578494785, 0.09373162411398223),
                            LogNormal(-0.5742377578494785, 0.09373162411398223)),

    'Light activity': mc.Activity(LogNormal(0.21380242785625422,0.09435378091059601),
                                  LogNormal(0.21380242785625422,0.09435378091059601)),

    'Moderate activity': mc.Activity(LogNormal(0.551771330362601, 0.1894616357138137),
                                     LogNormal(0.551771330362601, 0.1894616357138137)),

    'Heavy exercise': mc.Activity(LogNormal(1.1644665696723049, 0.21744554768657565),
                                  LogNormal(1.1644665696723049, 0.21744554768657565)),
}


# From CERN-OPEN-2021-04 and refererences therein
symptomatic_vl_frequencies = LogCustomKernel(
    np.array((2.46032, 2.67431, 2.85434, 3.06155, 3.25856, 3.47256, 3.66957, 3.85979, 4.09927, 4.27081,
     4.47631, 4.66653, 4.87204, 5.10302, 5.27456, 5.46478, 5.6533, 5.88428, 6.07281, 6.30549,
     6.48552, 6.64856, 6.85407, 7.10373, 7.30075, 7.47229, 7.66081, 7.85782, 8.05653, 8.27053,
     8.48453, 8.65607, 8.90573, 9.06878, 9.27429, 9.473, 9.66152, 9.87552)),
    np.array((0.001206885, 0.007851618, 0.008078144, 0.01502491, 0.013258014, 0.018528495, 0.020053765,
     0.021896167, 0.022047184, 0.018604005, 0.01547796, 0.018075445, 0.021503523, 0.022349217,
     0.025097721, 0.032875078, 0.030594727, 0.032573045, 0.034717482, 0.034792991,
     0.033267721, 0.042887485, 0.036846816, 0.03876473, 0.045016819, 0.040063473, 0.04883754,
     0.043944602, 0.048142864, 0.041588741, 0.048762031, 0.027921732, 0.033871788,
     0.022122693, 0.016927718, 0.008833228, 0.00478598, 0.002807662)),
    kernel_bandwidth=0.1
)


# From CERN-OPEN-2021-04 and refererences therein
virus_distributions = {
    'SARS_CoV_2': mc.SARSCoV2(
                viral_load_in_sputum=symptomatic_vl_frequencies,
                infectious_dose=100,
                viable_to_RNA=Uniform(0.15, 0.45),
                ),
    'SARS_CoV_2_B117': mc.SARSCoV2(
                viral_load_in_sputum=symptomatic_vl_frequencies,
                infectious_dose=60,
                viable_to_RNA=Uniform(0.15, 0.45),
                ),
    'SARS_CoV_2_P1': mc.SARSCoV2(
                viral_load_in_sputum=symptomatic_vl_frequencies,
                infectious_dose=100/2.25,
                viable_to_RNA=Uniform(0.15, 0.45),
                ),
    'SARS_CoV_2_B16172': mc.SARSCoV2(
                viral_load_in_sputum=symptomatic_vl_frequencies,
                infectious_dose=60/1.6,
                viable_to_RNA=Uniform(0.15, 0.45),
                ),
}


# From:
# https://doi.org/10.1080/02786826.2021.1890687
# https://doi.org/10.1016/j.jhin.2013.02.007
# https://doi.org/10.4209/aaqr.2020.08.0531
mask_distributions = {
    'Type I': mc.Mask(Uniform(0.25, 0.80)),
    'FFP2': mc.Mask(Uniform(0.83, 0.91)),
}
