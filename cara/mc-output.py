from cara.montecarlo import *
from cara.model_scenarios import *

compare_concentration_curves([classroom_model, classroom_model_with_hepa], ['Just window', 'Window and HEPA'])

#print(np.mean(chorale_model.infection_probability()))
#print(np.mean(chorale_model.infection_probability())+np.std(chorale_model.infection_probability()))
#print(np.quantile(chorale_model.infection_probability(),0.8))
#print(np.quantile(chorale_model.infection_probability(),0.90))
#print(np.quantile(chorale_model.infection_probability(),0.1))



#print(np.mean(exposure_models_2[1].infection_probability()))
#plot_pi_vs_viral_load([exposure_models[1],exposure_models_2[1]], labels=['B.1.1.7 - Guideline', 'B.1.1.7 - w/o masks'])
# plot_pi_vs_viral_load([shared_office_model[1]], labels=['Baseline, qID=60', 'HEPA, qID=60', 'No mask + windows closed, qID=60'],title='$P(I|qID)$ - Shared office scenario')


#generate_cdf_curves_vs_qr(masked=False,qid=1000)

# rs = [model.expected_new_cases() for model in large_population_baselines]
# print(f"R0 - original variant:\t{np.mean(rs[0])}")
# print(f"R0 - english variant:\t{np.mean(rs[1])}")
# print(f"Ratio between R0's:\t\t{np.mean(rs[1]) / np.mean(rs[0])}")
#
# compare_infection_probabilities_vs_viral_loads(*exposure_models)
#
#
#present_model(exposure_models[0].concentration_model)
# plot_pi_vs_qid(fixed_vl_exposure_models, labels=['Viral load = $10^{' + str(i) + '}$' for i in range(6, 11)],
#                qid_min=5, qid_max=2000, qid_samples=200)
#
# plot_pi_vs_qid(fixed_vl_exposure_models, labels=['Viral load = $10^{' + str(i) + '}$' for i in range(6, 11)],
#                qid_min=100, qid_max=400, qid_samples=100)
#
#
# plot_pi_vs_viral_load(exposure_models, labels=['Without masks', 'With masks'])
#
# for model in exposure_models:
#     present_model(model.concentration_model, title=f'Model summary - {"English" if model.concentration_model.infected.qid == 60 else "Original"} variant')
#     plt.hist(model.infection_probability(), bins=200)
#     plt.xlabel('Percentage probability of infection')
#     plt.title(f'Probability of infection in baseline case - {"English" if model.concentration_model.infected.qid == 60 else "Original"} variant')
#     plt.yticks([], [])
#     plt.show()
