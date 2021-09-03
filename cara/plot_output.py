""" Title: COVID Airborne Risk Assessment
Author: <author(s) names>
Date: <date>
Code version: <code version>
Availability: <where it's located> """

from cara.montecarlo import *
from cara.test_plots import *

# Exhaled virions while talking, seated #
print('\n<<<<<<<<<<< Vlout for Talking, seated >>>>>>>>>>>')
exposure_model_from_vl_talking()

# Exhaled virions while breathing, seated #
print('\n<<<<<<<<<<< Vlout for Breathing, seated >>>>>>>>>>>')
exposure_model_from_vl_breathing()

# Exhaled virions while talking according to BLO model, seated #
print('\n<<<<<<<<<<< Vlout for Talking, seated with chosen Cn,L >>>>>>>>>>>')
exposure_model_from_vl_talking_cn()

# Exhaled virions while breathing according to BLO model, seated #
print('\n<<<<<<<<<<< Vlout for Breathing, seated with chosen Cn,B >>>>>>>>>>>')
exposure_model_from_vl_breathing_cn()

############ Used for testing ############
#exposure_model_from_vl_talking_new_points()
