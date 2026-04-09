import typing
import numpy as np
import matplotlib.pyplot as plt

import caimira.ventilation.get_models as get_models
import caimira.ventilation.model_response as model_response
import caimira.ventilation.find_air_exch as find_air_exch
from caimira.ventilation.scenarios import ScenarioVar

figsize_prob = (7,6)
figsize_conc = (8,6)
titlesize = 16
fontsize = 14
ticksize = 12

def plot_probabilities(
    scenario: ScenarioVar,
    lim_probability_infection_list: list[float],  
    air_exch_list: list[float] = list(range(0, 60, 2)),
    title: str = "",
    plot_dose: bool = False
    ):

    infection_probability = [model_response.calculate_infection_probability(air_exch_values=[air_exch], scenario=scenario) for air_exch in air_exch_list]

    print(f"60 ACH   =>   P(I) = {model_response.calculate_infection_probability(air_exch_values=[60], scenario=scenario)*100:.2f}%, Dose = {model_response.calculate_deposited_exposure(air_exch_values=[60], scenario=scenario):.2f}")

    fig, ax1 = plt.subplots(1, 1, figsize=figsize_prob)

    ax1.plot(
        air_exch_list,
        infection_probability,
        linewidth=2,
        color="tab:blue",
        label="Infection probability P(I)"
    )
    ax1.set_ylabel('Infection probability P(I)', color='tab:blue', fontsize=fontsize)
    ax1.tick_params(axis='y', labelcolor='tab:blue', labelsize=ticksize)
    ax1.set_xlabel("air exchange per hour", fontsize=fontsize)
    ax1.tick_params(axis='x', labelsize=ticksize)
    ax1.grid(True, linestyle="--", alpha=0.6)

    if plot_dose:
        dose_list = [model_response.calculate_deposited_exposure(air_exch_values=[air_exch], scenario=scenario) for air_exch in air_exch_list]
        ax2 = ax1.twinx()

        ax2.plot(
            air_exch_list,
            dose_list,
            linewidth=2,
            color="tab:red",
            label="Dose",
            linestyle="--"
        )
        ax2.set_ylabel('Viral dose', color='tab:red', fontsize=fontsize)
        ax2.tick_params(axis='y', labelcolor='tab:red', labelsize=ticksize)

    else:
        exposure_model = get_models.get_exposure_model(air_exch_list[:1], model_response.first_vent_transition_times(scenario), scenario).build_model(1)
        clean_air_per_sec_per_pers = find_air_exch.clean_air_per_sec_per_pers(air_exch_list, exposure_model)

        ax2 = ax1.twiny()
        ax2.plot(
                clean_air_per_sec_per_pers,
                infection_probability,
                linewidth=2,
                color="tab:blue",
                label="Infection probability P(I)"
            )
        ax2.set_xlabel("clean air delivery (L/s/person)", fontsize=fontsize)
        ax2.tick_params(axis='x', labelsize=ticksize)
        ax2.xaxis.set_ticks_position('bottom')
        ax2.xaxis.set_label_position('bottom')
        ax2.spines['bottom'].set_position(('outward', 40))
        ax2.spines['top'].set_visible(False)

    for lim_probability_infection in lim_probability_infection_list:
        if lim_probability_infection > 0:
            lim_air_exch, probability = find_air_exch.find_constant_air_exch(scenario, lim_probability_infection, hi=air_exch_list[-1])

            ax1.plot(
                lim_air_exch,
                probability,
                "o",
                color="k",
                markersize=8,
            )

            ax1.annotate(
                #f"P(I) limit: {lim*100}% \n({lim_air_exch:.1f}, {probability:.2%})",
                f"({lim_air_exch:.1f}, {probability:.1%})",
                xy=(lim_air_exch, probability),
                xytext=(5, 5),           
                textcoords="offset points",
                fontsize=fontsize,
                color="k"
            )

            if plot_dose:
                dose = model_response.calculate_deposited_exposure(air_exch_values=[lim_air_exch], scenario=scenario)

                ax2.plot(
                    lim_air_exch,
                    dose,
                    "o",
                    color="k",
                    markersize=8,
                )

                ax2.annotate(
                    f"({lim_air_exch:.1f}, {dose:.1f})",
                    xy=(lim_air_exch, dose),
                    xytext=(5, 5),           
                    textcoords="offset points",
                    fontsize=fontsize,
                    color="k"
                )

    lines = ax1.get_lines() 
    if plot_dose:
        lines += ax2.get_lines()
    labels = [line.get_label() for line in lines]
    ax1.legend(lines, labels, fontsize=fontsize) # type: ignore
    plt.title(title, fontsize=titlesize)
    plt.tight_layout()
    plt.show()

def plot_model_concentration_results(
        scenario: ScenarioVar,
        air_exch_list: list[float], 
        vent_transition_times: typing.Optional[list] = None,  
        title: str = "",
        viral_values: bool = True, 
        CO2_values: bool = True,
        deterministic_CO2: bool = True,
        plot_air_exch: bool = True,
        plot_clean_air_delivery: bool = True,
    ):
    if not isinstance(air_exch_list, list):
        air_exch_list = [air_exch_list]
        
    if not vent_transition_times:
        vent_transition_times = model_response.first_vent_transition_times(scenario)
    axviral_ymax = 0.
    exposure_model, times, concentrations, pi = model_response.model_concentration_results(scenario, air_exch_list, vent_transition_times, viral_values, CO2_values, deterministic_CO2)
    concentrations_viral, concentrations_CO2 = concentrations
    ############ Combined plot: Viral concentration + CO2 ############
    _, axviral = plt.subplots(figsize=figsize_conc)

    # ===== Viral concentration (LEFT AXIS) =====
    mean_viral = [np.mean(c) for c in concentrations_viral]
    axviral.plot(
        times,
        mean_viral,
        color='tab:blue',
        label='Viral concentration'
    )
    axviral.set_xlabel('Time of day', fontsize=fontsize)
    axviral.set_ylabel('Viral concentration (IRP / m³)', color='tab:blue', fontsize=fontsize)
    axviral.tick_params(axis='y', labelcolor='tab:blue', labelsize=ticksize)
    if max(mean_viral)*1.1 > axviral_ymax:
        axviral_ymax = max(mean_viral)*1.1
    axviral.set_ylim((0,axviral_ymax))

    clean_air_delivery = find_air_exch.clean_air_per_sec_per_pers(air_exch_list, exposure_model)
    print(f"Air changes per hour: Mean: {np.mean(air_exch_list)}, All values: {[round(air_exch, 2) for air_exch in air_exch_list]}")
    print(f"Clean air delivery (L/s/person): Mean: {np.mean([[cld for cld in clean_air_delivery if isinstance(cld, float)]])}, All values: {[round(cld, 2) if type(cld)==float else cld for cld in clean_air_delivery]}")

    axes = []
    if CO2_values:
        axco2 = axviral.twinx()
        if isinstance(concentrations_CO2[0], float):
            mean_CO2 = concentrations_CO2
        else:
            mean_CO2 = [np.mean(c) for c in concentrations_CO2]
        print(f"Max CO2: {np.max(mean_CO2):.2f}")
        axco2.plot(
            times,
            mean_CO2,
            color='tab:red',
            label='CO₂ concentration'
        )
        axco2.set_ylabel('CO₂ concentration (ppm)', color='tab:red', fontsize=fontsize)
        axco2.tick_params(axis='y', labelcolor='tab:red', labelsize=ticksize)
        axco2_ymax = 0.
        if deterministic_CO2:
            new_axco2_ymax = max(concentrations_CO2)*1.1
            if new_axco2_ymax > axco2_ymax:
                axco2_ymax = new_axco2_ymax
            axco2.set_ylim((440,axco2_ymax))
        else:
            new_axco2_ymax = max([np.quantile(c, 0.95) for c in concentrations_CO2])*1.1
            if new_axco2_ymax > axco2_ymax:
                axco2_ymax = new_axco2_ymax
            axco2.set_ylim((440,axco2_ymax))

            axco2.fill_between(
                times,
                [np.quantile(c, 0.05) for c in concentrations_CO2],
                [np.quantile(c, 0.95) for c in concentrations_CO2],
                color='tab:red',
                alpha=0.2
            )
        axes.append(axco2)

    if CO2_values and (plot_air_exch or plot_clean_air_delivery):
        axco2.spines["right"].set_visible(False)
        axco2.spines["left"].set_visible(True)
        axco2.yaxis.set_label_position("left")
        axco2.yaxis.set_ticks_position("left")
        axco2.spines["left"].set_position(("outward", 60))
            
    if plot_air_exch:
        axaex = axviral.twinx()
        extended_air_exch_list = find_air_exch.carry_forward_air_change_times(air_exch_list, vent_transition_times, times)

        assert len(times) == len(extended_air_exch_list) + 1
        extended_air_exch_list.append(extended_air_exch_list[-1])
        axaex.plot(
            times,
            extended_air_exch_list,
            color='tab:green',
            label='air exchange per hour'
        )
        axaex.set_ylabel('air exchange per hour', color='tab:green', fontsize=fontsize)
        axaex.tick_params(axis='y', labelcolor='tab:green', labelsize=ticksize)
        axaex_ymax = 0.

        new_axaex_ymax = max(extended_air_exch_list)*1.15
        if new_axaex_ymax > axaex_ymax:
            axaex_ymax = new_axaex_ymax
        axaex.set_ylim((0,axaex_ymax))
        axes.append(axaex)

    if plot_clean_air_delivery:
        axcad = axviral.twinx()
        extended_air_exch_list = find_air_exch.carry_forward_air_change_times(air_exch_list, vent_transition_times, times)
        clean_air_delivery = find_air_exch.clean_air_per_sec_per_pers(extended_air_exch_list, exposure_model)

        assert len(times) == len(clean_air_delivery) + 1
        clean_air_delivery.append(np.inf)
        clean_air_delivery_float = list(np.where(np.isfinite(np.array(clean_air_delivery)), np.array(clean_air_delivery), np.nan))
        axcad.plot(
            times,
            clean_air_delivery_float,
            color='tab:orange',
            label='clean air delivery'
        )
        axcad.set_ylabel('clean air delivery (L/s/person)', color='tab:orange', fontsize=fontsize)
        axcad.tick_params(axis='y', labelcolor='tab:orange', labelsize=ticksize)
        axcad_ymax = 0.

        new_axcad_ymax = max(clean_air_delivery_float)*1.2
        if new_axcad_ymax > axcad_ymax:
            axcad_ymax = new_axcad_ymax
        axcad.set_ylim((0,axcad_ymax))
        axes.append(axcad)

        if plot_air_exch:
            axcad.spines["right"].set_position(("outward", 60))

    axviral.text(
    0.95, 0.05,                     # (x, y) in axes coordinates
    f"P(I)={pi:.1%}",
    transform=axviral.transAxes,       # use axes fraction (0–1)
    fontsize=fontsize,
    ha='right',                    # align right
    va='bottom',                   # align bottom
    bbox=dict(
        boxstyle="round",
        facecolor="white",
        alpha=0.8
    )
)

    axviral.tick_params(axis='x', labelsize=ticksize)
    lines = axviral.get_lines()
    for ax in axes:
        lines += ax.get_lines()

    labels = [line.get_label() for line in lines]
    axviral.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=fontsize) # type: ignore
    plt.title(title, fontsize=titlesize)
    plt.tight_layout()
    plt.show()