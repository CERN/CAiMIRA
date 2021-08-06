""" Title: COVID Airborne Risk Assessment
Author: <author(s) names>
Date: <date>
Code version: <code version>
Availability: <where it's located> """

from cara.montecarlo import *
from cara.model_scenarios_publication import *

# qR table:
generate_qr_csv('qR_unmasked')
generate_qr_csv('qr_masked', masked=True)

# qR values for Breathing, light activity:
print('\n<<<<<<<<<<< qR for Breathing, light activity >>>>>>>>>>>')
present_qR_values(qR_models[0].concentration_model)
# qR values for Speaking, light activity:
print('\n<<<<<<<<<<< qR for Speaking, light activity >>>>>>>>>>>')
present_qR_values(qR_models[1].concentration_model)
# qR values for Shouting, light activity:
print('\n<<<<<<<<<<< qR for Shouting / Singing, light activity >>>>>>>>>>>')
present_qR_values(qR_models[2].concentration_model)

# qR values for shouting and light activity - qID=100, 500 and 1000
print('\n<<<<<<<<<<< Shouting and light activity - qID=100 >>>>>>>>>>>')
present_qR_values(qR_models_shout_light[0].concentration_model)
print('\n<<<<<<<<<<< Shouting and light activity - qID=500 >>>>>>>>>>>')
present_qR_values(qR_models_shout_light[1].concentration_model)
print('\n<<<<<<<<<<< Shouting and light activity - qID=1000 >>>>>>>>>>>')
present_qR_values(qR_models_shout_light[2].concentration_model)
print('\n<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>')

present_model(qR_models[2].concentration_model, title='')

# qR for the S V Chorale superspreading event
print('\n<<<<<<<<<<< S V Chorale: Shouting and light activity - qID=100 >>>>>>>>>>>')
present_qR_quantiles(qR_models_shout_light[0].concentration_model, quantile=0.8)

# CDF plots of qR
generate_cdf_curves_vs_qr(masked=False,qid=100)
generate_cdf_curves_vs_qr(masked=False,qid=500)
generate_cdf_curves_vs_qr(masked=False,qid=1000)


