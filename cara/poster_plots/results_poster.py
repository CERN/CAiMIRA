""" Title: CARA - COVID Airborne Risk Assessment
Author: A. Henriques et al
Date: 03/31/2022
Code version: 4.0.0 """

from model_scenarios_poster import *
from scripts_poster import *

############# PLOTS ############

#### Generic P(I) vs vl plot
#plot_pi_vs_viral_load(activity='Heavy exercise', expiration='Shouting', mask='No mask')
plot_pi_vs_viral_load_box_plot(activity='Heavy exercise', expiration='Shouting', mask='No mask')


### Paper classroom scenarios concentration curves
# compare_concentration_curves(models = [
#                                       classroom_model_lunch_vent(mask='No mask', lunch_break=False, ventilation=False, hepa=False),
#                                       classroom_model_lunch_vent(mask='Type I', lunch_break=True, ventilation=False, hepa=False),
#                                       classroom_model_lunch_vent(mask='Type I', lunch_break=True, ventilation=True, hepa=False),
#                                       classroom_model_lunch_vent(mask='Type I', lunch_break=True, ventilation=True, hepa=True),
#                                       ],
#                            labels = ['no measures', 'mask and break',
#                                       'Type I Masks, ventilation, break', 'Type I Masks and ventilation, break, hepa'],
#                            colors = ['salmon', 'royalblue', (0, 0, 0.54, 1), (0, 0., 0.54, 0.4)])