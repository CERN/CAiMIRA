""" Title: COVID Airborne Risk Assessment
Author: <author(s) names>
Date: <date>
Code version: <code version>
Availability: <where it's located> """

from cara.models import ExposureModel, InfectedPopulation
from cara import model_scenarios_paper
from cara.results_paper import *
from cara.monte_carlo.data import symptomatic_vl_frequencies
from itertools import product
from dataclasses import dataclass

# Exhaled virions while talking, seated #
#print('\n<<<<<<<<<<< Vlout for Talking, seated >>>>>>>>>>>')
#exposure_model_from_vl(activity='Seated', expiration='Talking', mask='No mask')

# Exhaled virions while breathing, seated #
#print('\n<<<<<<<<<<< Vlout for Breathing, seated >>>>>>>>>>>')
#exposure_model_from_vl(activity='Seated', expiration='Breathing', mask='No mask')

# Exhaled virions while breathing, light activity #
#print('\n<<<<<<<<<<< Vlout for Shouting, light activity >>>>>>>>>>>')
#exposure_model_from_vl(activity='Light activity', expiration='Shouting', mask='No mask')

# Exhaled virions while talking according to BLO model, seated #
#print('\n<<<<<<<<<<< Vlout for Talking, seated with chosen Cn,L >>>>>>>>>>>')
#exposure_model_from_vl_cn(activity='Seated', expiration='Talking', mask='No mask')
#print('\n')

# Exhaled virions while breathing according to BLO model, seated #
#print('\n<<<<<<<<<<< Vlout for Breathing, seated with chosen Cn,B >>>>>>>>>>>')
#exposure_model_from_vl_cn(activity='Seated', expiration='Breathing', mask='No mask')
#print('\n')

############ Plots with viral loads and emission rates + statistical data ############
#present_vl_er_histograms(activity='Seated', mask='No mask')
#present_vl_er_histograms(activity='Light activity', mask='No mask')
#present_vl_er_histograms(activity='Heavy exercise', mask='No mask')

############ CDFs for comparing the ER-Values in different scenarios ############
#generate_cdf_curves()

############ Deposition Fraction Graph ############
#print('\n<<<<<<<<<<< Deposition Fraction for Breathing, seated >>>>>>>>>>>') 
#calculate_deposition_factor()

############ Comparison between concentration curves ############ 
#compare_concentration_curves()

############ Emission Rate Violin plot ############ 
#compare_viruses_vr()

############ Probability of infection vs Viral load ############ 
plot_pi_vs_viral_load(activity='Seated', expiration='Talking', mask='No mask')

############ Used for testing ############
#exposure_model_from_vl_talking_new_points()
