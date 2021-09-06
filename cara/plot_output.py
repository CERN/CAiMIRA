""" Title: COVID Airborne Risk Assessment
Author: <author(s) names>
Date: <date>
Code version: <code version>
Availability: <where it's located> """

from cara import model_scenarios_paper
from cara.results_paper import *
from cara.test_plots import *

# Exhaled virions while talking, seated #
print('\n<<<<<<<<<<< Vlout for Talking, seated >>>>>>>>>>>')
#exposure_model_from_vl_talking()

# Exhaled virions while breathing, seated #
print('\n<<<<<<<<<<< Vlout for Breathing, seated >>>>>>>>>>>')
#exposure_model_from_vl_breathing()

# Exhaled virions while talking according to BLO model, seated #
print('\n<<<<<<<<<<< Vlout for Talking, seated with chosen Cn,L >>>>>>>>>>>')
#exposure_model_from_vl_talking_cn()

# Exhaled virions while breathing according to BLO model, seated #
print('\n<<<<<<<<<<< Vlout for Breathing, seated with chosen Cn,B >>>>>>>>>>>')
#exposure_model_from_vl_breathing_cn()
print('\n')
############ Statistical Data ############

############ Breathing model ############
exposure_mc = model_scenarios_paper.breathing_exposure()
exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(cn_B=0.06, cn_L=0.2)
print('\n<<<<<<<<<<< Breathing model statistics >>>>>>>>>>>')
print_er_info(emission_rate)

############ Talking model ############
exposure_mc = model_scenarios_paper.talking_exposure()
exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(cn_B=0.06, cn_L=0.2)
print('\n<<<<<<<<<<< Talking model statistics >>>>>>>>>>>')
print_er_info(emission_rate)

############ Used for testing ############
#exposure_model_from_vl_talking_new_points()
