""" Title: COVID Airborne Risk Assessment
Author: <author(s) names>
Date: <date>
Code version: <code version>
Availability: <where it's located> """

from cara import model_scenarios_paper
from cara.results_paper import *
from cara.test_plots import *
from cara.monte_carlo.data import symptomatic_vl_frequencies

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
breathing_er = [np.log10(er) for er in emission_rate]
print('\n<<<<<<<<<<< Breathing model statistics >>>>>>>>>>>')
print_er_info(emission_rate)

############ Speaking model ############
exposure_mc = model_scenarios_paper.speaking_exposure()
exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(cn_B=0.06, cn_L=0.2)
speaking_er = [np.log10(er) for er in emission_rate]
print('\n<<<<<<<<<<< Speaking model statistics >>>>>>>>>>>')
print_er_info(emission_rate)

############ Shouting model ############
exposure_mc = model_scenarios_paper.shouting_exposure()
exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(cn_B=0.06, cn_L=0.2)
shouting_er = [np.log10(er) for er in emission_rate]
print('\n<<<<<<<<<<< Shouting model statistics >>>>>>>>>>>')
print_er_info(emission_rate)


############ Plots with Viral loads and emission rates
viral_load_in_sputum = exposure_model.concentration_model.infected.virus.viral_load_in_sputum
present_vl_er_histograms(viral_load_in_sputum, breathing_er, speaking_er, shouting_er)


############ Used for testing ############
#exposure_model_from_vl_talking_new_points()
