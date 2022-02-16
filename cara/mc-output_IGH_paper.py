from cara.montecarlo import *
from cara.model_scenarios_IGH_paper import *

#Fig 1c
# compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed[0],classroom_model_IGH_no_mask_windows_open_breaks[0],
#                              classroom_model_IGH_no_mask_windows_open_alltimes[0]],
#                             labels=['Windows closed', 'Window open during breaks', 'Window open at all times'],
#                             colors=['tomato', 'lightskyblue', 'limegreen', '#1f77b4', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                             title='No mask - Spring/Summer period'
#                             )
# print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
# print_qd_info(classroom_model_IGH_no_mask_windows_open_breaks[0])
# print_qd_info(classroom_model_IGH_no_mask_windows_open_alltimes[0])

#Fig 1d
# compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed_winter[0],classroom_model_IGH_no_mask_windows_open_breaks_winter[0],
#                              classroom_model_IGH_no_mask_windows_open_alltimes_winter[0], classroom_model_IGH_no_mask_windows_fully_open_alltimes_winter[0]],
#                             labels=['Windows closed', 'Window fully open during breaks', 'Window slightly open at all times', 'Window fully open at all times'],
#                             colors=['tomato', 'lightskyblue', '#1f77b4', 'limegreen', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                             title='No mask - Winter period'
#                             )
# print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
# print_qd_info(classroom_model_IGH_no_mask_windows_open_breaks_winter[0])
# print_qd_info(classroom_model_IGH_no_mask_windows_open_alltimes_winter[0])
# print_qd_info(classroom_model_IGH_no_mask_windows_fully_open_alltimes_winter[0])

##Fig 1e
#compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed[0],classroom_model_IGH_no_mask_2windows_open_breaks[0],
#                              classroom_model_IGH_no_mask_2windows_open_alltimes[0]],
#                             labels=['Windows closed', '2 windows open during breaks', '2 windows open at all times'],
#                             colors=['tomato', 'lightskyblue', 'limegreen', '#1f77b4', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                             title='No mask - Spring/Summer period'
#                             )
#print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
#print_qd_info(classroom_model_IGH_no_mask_2windows_open_breaks[0])
#print_qd_info(classroom_model_IGH_no_mask_2windows_open_alltimes[0])

##Fig 1f
# compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed_winter[0],classroom_model_IGH_no_mask_2windows_open_breaks_winter[0],
#                              classroom_model_IGH_no_mask_2windows_open_alltimes_winter[0], classroom_model_IGH_no_mask_2windows_fully_open_alltimes_winter[0]],
#                             labels=['Windows closed', '2 windows fully open during breaks', '2 windows slighty open at all times', '2 windows fully open at all times'],
#                             colors=['tomato', 'lightskyblue', '#1f77b4', 'limegreen', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                             title='No mask - Winter period'
#                             )
# print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
# print_qd_info(classroom_model_IGH_no_mask_2windows_open_breaks_winter[0])
# print_qd_info(classroom_model_IGH_no_mask_2windows_open_alltimes_winter[0])
# print_qd_info(classroom_model_IGH_no_mask_2windows_fully_open_alltimes_winter[0])

##Fig 1g
#compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed[0],classroom_model_IGH_no_mask_6windows_open_breaks[0],
#                              classroom_model_IGH_no_mask_6windows_open_alltimes[0]],
#                             labels=['Windows closed', '6 windows open during breaks', '6 windows open at all times'],
#                             colors=['tomato', 'lightskyblue', 'limegreen', '#1f77b4', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                             title='No mask - Spring/Summer period'
#                             )
#print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
#print_qd_info(classroom_model_IGH_no_mask_6windows_open_breaks[0])
#print_qd_info(classroom_model_IGH_no_mask_6windows_open_alltimes[0])
#
##Fig 1h
#compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed_winter[0],classroom_model_IGH_no_mask_6windows_open_breaks_winter[0],
#                              classroom_model_IGH_no_mask_6windows_open_alltimes_winter[0], classroom_model_IGH_no_mask_6windows_fully_open_alltimes_winter[0]],
#                             labels=['Windows closed', '6 windows fully open during breaks', '6 windows slighty open at all times', '6 windows fully open at all times'],
#                             colors=['tomato', 'lightskyblue', '#1f77b4', 'limegreen', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                             title='No mask - Winter period'
#                             )
#print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
#print_qd_info(classroom_model_IGH_no_mask_6windows_open_breaks_winter[0])
#print_qd_info(classroom_model_IGH_no_mask_6windows_open_alltimes_winter[0])
#rint_qd_info(classroom_model_IGH_no_mask_6windows_fully_open_alltimes_winter[0])

##Fig 1i
#compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed[0],
#                             classroom_model_IGH_no_mask_6windows_open_breaks_endOfClass[0]],
#                             labels=['Windows closed',
#                                     '6 windows open during breaks + end of classes'],
#                             colors=['tomato', '#1f77b4'],
#                             title='Without mask - Spring/Summer period'
#                             )
#
#print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
##print_qd_info(classroom_model_IGH_no_mask_6windows_open_alltimes[0])
#print_qd_info(classroom_model_IGH_no_mask_6windows_open_breaks_endOfClass[0])

##Fig 1j
#compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed_winter[0],
#                             classroom_model_IGH_no_mask_6windows_open_breaks_endOfClass_winter[0]],
#                             labels=['Windows closed',
#                                     '6 windows open during breaks + end of classes'],
#                             colors=['tomato', '#1f77b4'],
#                             title='Without mask - Winter period'
#                             )
#
#print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
#print_qd_info(classroom_model_IGH_no_mask_6windows_open_alltimes_winter[0])
#print_qd_info(classroom_model_IGH_no_mask_6windows_open_breaks_endOfClass_winter[0])



##Fig 2a
# compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed[0],classroom_model_IGH_no_mask_windows_closed_1HEPA[0],
#                              classroom_model_IGH_no_mask_windows_closed_2HEPA[0]],
#                             labels=['Windows closed', 'Windows closed + 1 HEPA filter (2.5 ACH)', 'Windows closed + 2 HEPA filter (5 ACH)'],
#                             colors=['tomato', 'lightskyblue', 'limegreen', '#1f77b4', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                             title='No mask'
#                             )
# print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
# print_qd_info(classroom_model_IGH_no_mask_windows_closed_1HEPA[0])
# print_qd_info(classroom_model_IGH_no_mask_windows_closed_2HEPA[0])

#Fig 2b
# compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed[0],classroom_model_IGH_with_mask_windows_closed[0]],
#                             labels=['Windows closed', 'Windows closed + surgical type masks'],
#                             colors=['tomato', 'lightskyblue', 'limegreen', '#1f77b4', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                             title='Use of mask'
#                             )
# print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
# print_qd_info(classroom_model_IGH_with_mask_windows_closed[0])


##Fig 3b
# compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed[0],classroom_model_IGH_no_mask_2windows_open_alltimes_winter_bis[0],
#                              classroom_model_IGH_with_mask_2windows_open_alltimes_winter[0]],
#                             labels=['Windows closed', '2 windows open at all times', '2 windows open at all times + surgical masks'],
#                             colors=['tomato', 'lightskyblue', 'limegreen', '#1f77b4', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                             title='Combination of measures (winter period) '
#                             )
#print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
#print_qd_info(classroom_model_IGH_no_mask_2windows_open_alltimes_winter_bis[0])
#print_qd_info(classroom_model_IGH_with_mask_2windows_open_alltimes_winter[0])

##Fig 3c
# compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed[0],classroom_model_IGH_with_mask_windows_closed_1HEPA[0],
#                               classroom_model_IGH_with_mask_windows_closed_2HEPA[0]],
#                              labels=['No masks', '1 HEPA filter (2.5 ACH) + surgical masks', '2 HEPA filter (5 ACH) + surgical masks'],
#                              colors=['tomato', 'lightskyblue', 'limegreen', '#1f77b4', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                              title='Combination of measures (windows closed) '
#                              )
#
# print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
# print_qd_info(classroom_model_IGH_with_mask_windows_closed_1HEPA[0])
# print_qd_info(classroom_model_IGH_with_mask_windows_closed_2HEPA[0])

##Fig 3d
# compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed[0],classroom_model_IGH_with_mask_2windows_open_alltimes_winter_1HEPA[0],
#                              classroom_model_IGH_with_mask_2windows_open_alltimes_winter_2HEPA[0]],
#                             labels=['Windows closed', '2 windows open at all times + 1 HEPA filter (2.5 ACH) + surgical masks', '2 windows open at all times + 2 HEPA filter (5 ACH) + surgical masks'],
#                             colors=['tomato', 'lightskyblue', 'limegreen', '#1f77b4', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                             title='Combination of measures (winter period) '
#                             )
#print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
#print_qd_info(classroom_model_IGH_with_mask_2windows_open_alltimes_winter_1HEPA[0])
#print_qd_info(classroom_model_IGH_with_mask_2windows_open_alltimes_winter_2HEPA[0])
#



#>>>>>>>>>>> Aux >>>>>>>>

#print_qd_info(classroom_model_IGH_no_mask_2windows_open_breaks_endOfClass_winter[0])
#print_qd_info(classroom_model_IGH_no_mask_windows_open_breaks_endOfClass_winter[0])
#print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])

#print_qd_info(classroom_model_IGH_no_mask_windows_closed[0])
#print_qd_info(classroom_model_IGH_no_mask_6windows_open_breaks_endOfClass[0])
#print_qd_info(classroom_model_IGH_no_mask_2windows_open_breaks_endOfClass_winter[0])
#print_qd_info(classroom_model_IGH_no_mask_windows_open_breaks_endOfClass_winter[0])

# compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed[0],classroom_model_IGH_no_mask_2windows_open_breaks_winter_bis[0],
#                              classroom_model_IGH_with_mask_2windows_open_breaks_winter[0]],
#                             labels=['Windows closed', '2 windows open during breaks', '2 windows open during breaks + surgical masks'],
#                             colors=['tomato', 'lightskyblue', 'limegreen', '#1f77b4', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                             title='Combination of measures (winter period) '
#                             )

# compare_concentration_curves_virus_IGH_paper([classroom_model_IGH_no_mask_windows_closed[0],classroom_model_IGH_with_mask_2windows_open_breaks_winter_1HEPA[0],
#                              classroom_model_IGH_with_mask_2windows_open_breaks_winter_2HEPA[0]],
#                             labels=['Windows closed', '2 windows open during breaks + 1 HEPA filter (2.5 ACH) + surgical masks', '2 windows open during breaks + 2 HEPA filter (5 ACH) + surgical masks'],
#                             colors=['tomato', 'lightskyblue', 'limegreen', '#1f77b4', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                             title='Combination of measures (winter period) '
#                             )

#compare_concentration_curves([classroom_model_IGH_no_mask_windows_closed[1],classroom_model_IGH_no_mask_2windows_open_breaks[1],classroom_model_IGH_no_mask_2windows_open_breaks_endOfClass[1],
#                              classroom_model_IGH_no_mask_2windows_open_alltimes[1], classroom_model_IGH_no_mask_windows_closed_1HEPA[1],
#                              classroom_model_IGH_no_mask_windows_closed_2HEPA[1]],
#                             labels=['Windows closed', '2 Windows open during breaks', '2 Windows open during breaks + end of classes',
#                                     '2 Windows open at all times', 'Windows closed + HEPA filter (2.5 ACH)', 'Windows closed + HEPA filter (5 ACH)'],
#                             colors=['tomato','limegreen', '#1f77b4', 'seagreen', 'lightskyblue', 'deepskyblue'],
#                             title='No mask - Spring/Summer period'
#                             )

#present_model(classroom_model_IGH_no_mask_windows_closed[0].concentration_model, title='')

