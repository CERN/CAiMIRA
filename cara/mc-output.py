from cara.montecarlo import *
from cara.model_scenarios import *

#plot_concentration_curve(classroom_model[1])
#compare_concentration_curves([classroom_model, classroom_model_with_hepa], ['Just window', 'Window and HEPA'])

#print(np.mean(classroom_model[0].infection_probability()))
#print(np.mean(classroom_model[1].infection_probability()))
#print(np.mean(chorale_model.infection_probability())+np.std(chorale_model.infection_probability()))
#print(np.quantile(chorale_model[0].infection_probability(),0.8))
#print(np.quantile(chorale_model.infection_probability(),0.90))
#print(np.quantile(chorale_model.infection_probability(),0.1))

#plot_pi_vs_exposure_time(chorale_model, ['model1', 'model2'])
#print(np.mean(ski_cabin_model_baseline_20[1].infection_probability()))
#plot_pi_vs_exposure_time(ski_cabin_model_baseline_exposure_time+ski_cabin_model_baseline_exposure_time_FFP2, ['Ski cabin - surgical masks', 'Ski cabin - no masks','Ski cabin - FFP2 masks',''],
#                         colors=['#1f77b4','tomato', 'seagreen', 'seagreen'],
#                         linestyles=['solid', 'dashed', '-.', '-.'],
#                         points=20,
#                         time_in_minutes=True,
#                         normalize_y_axis=True)

#compare_viruses_qr(violins=True)

#print_qd_info(waiting_room_model_full_winter[1])

#print(np.mean(shared_office_model[1].infection_probability()))
#composite_plot_pi_vs_viral_load([shared_office_worst_model[1], shared_office_model[1], shared_office_better_model[1]],
#                                 labels=['No mask &\nwindows closed', 'Baseline:Windows\nopen (10min/2h)', 'Windows open\n(10min/2h) +\nHEPA filter'],
#                                 colors=['tomato', '#1f77b4', 'limegreen'],
#                                 title='',
#                                 vl_points=200)
#composite_plot_pi_vs_viral_load([classroom_model_no_vent[1], classroom_model[1], classroom_model_with_hepa[1], classroom_model_full_open_multi[1], classroom_model_full_open_multi_masks[1]],
#                                 labels=['Windows closed', 'Baseline:Windows\nopen (10min/2h)', 'Windows open\n(10min/2h) + HEPA', 'Multiple windows open', 'Multiple windows open\n+masks'],
#                                 colors=['tomato','#1f77b4', 'dodgerblue', 'seagreen', 'limegreen'],
#                                 title='',
#                                 vl_points=200)

#composite_plot_pi_vs_viral_load([ski_cabin_model_60[1], ski_cabin_model_30[1], ski_cabin_model_baseline_20[1], ski_cabin_model_10[1]],
#                                 labels=['60 min', '30 min', 'Baseline: 20 min', '10 min'],
#                                 colors=['tomato', 'lightsalmon', '#1f77b4', 'limegreen'],
#                                 title='',
#                                 vl_points=200)
#
#composite_plot_pi_vs_viral_load([ski_cabin_model_baseline_20_no_mask[1], ski_cabin_model_baseline_20[1], ski_cabin_model_baseline_20_FFP2[1]],
#                                 labels=['20min\nno masks', 'Baseline: 20 min\nsurgical mask', '20 min\nFFP2 mask'],
#                                 colors=['tomato', '#1f77b4','seagreen'],
#                                 title='',
#                                 vl_points=200)

#compare_concentration_curves([classroom_model_no_vent[1], classroom_model[1], classroom_model_with_hepa[1], classroom_model_full_open_multi[1]],
#                             labels=['Windows closed', 'Baseline: Windows open (10min/2h)', 'Windows open (10min/2h) + HEPA', 'Multiple windows open'],
#                             colors=['tomato','#1f77b4', 'seagreen', 'limegreen'],
#                             title=''
#                             )
#
#compare_concentration_curves([waiting_room_model[1], waiting_room_model_full_summer[1],
#                              waiting_room_model_full_winter[1], waiting_room_model_periodic_winter[1]],
#                             labels=['Baseline: Windows closed', 'Windows open (summer)', 'Windows open (winter)', 'Windows open 5min/20min (winter)'],
#                             colors=['#1f77b4', 'darkorange', 'deepskyblue', 'lightskyblue'],
#                             title=''
#                             )

#plot_pi_vs_viral_load([shared_office_model[1]], labels=['Baseline'],title='')


#generate_cdf_curves_vs_qr(masked=False,qid=1000)

# rs = [model.expected_new_cases() for model in large_population_baselines]
# print(f"R0 - original variant:\t{np.mean(rs[0])}")
# print(f"R0 - english variant:\t{np.mean(rs[1])}")
# print(f"Ratio between R0's:\t\t{np.mean(rs[1]) / np.mean(rs[0])}")
#
# compare_infection_probabilities_vs_viral_loads(*exposure_models)
#
#
#present_model(exposure_models[0].concentration_model, title='')
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

#composite_plot_pi_vs_viral_load([shared_office_worst_model[1], shared_office_worst_model_infiltration[1]],
#                                 labels=['No mask &\nwindows closed', 'Baseline:Windows\nopen (10min/2h)', 'Windows open\n(10min/2h) +\nHEPA filter'],
#                                 colors=['tomato', '#1f77b4', 'limegreen'],
#                                 title='Shared office scenario',
#                                 vl_points=200)

generate_qr_csv('qR_unmasked')
generate_qr_csv('qr_masked', masked=True)
