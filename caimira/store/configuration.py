import asyncio
import os

from caimira.store.global_store import GlobalStore


class Configuration:
    '''
    Configuration to handle data. Contains the default values used in the model.
    Might suffer update from the Data Service.
    '''

    def __init__(self):
        self.data_fetched = False
        self.BLOmodel = {
            'cn': {'B': 0.06,
                   'L': 0.2,
                   'O': 0.0010008,
                   },
            'mu': {
                'B': 0.989541,
                'L': 1.38629,
                'O': 4.97673,
            },
            'sigma': {
                'B': 0.262364,
                'L': 0.506818,
                'O': 0.585005,
            },
        }
        self.activity_distributions = {
            'Seated': {
                'inhalation_rate': {
                    'associated_distribution': 'Numpy Log-normal Distribution (random.lognormal)',
                    'parameters': {'mean_gaussian': -0.6872121723362303, 'standard_deviation_gaussian': 0.10498338229297108},
                },
                'exhalation_rate': {
                    'associated_distribution': 'Numpy Log-normal Distribution (random.lognormal)',
                    'parameters': {'mean_gaussian': -0.6872121723362303, 'standard_deviation_gaussian': 0.10498338229297108},
                },
            },
            'Standing': {
                'inhalation_rate': {
                    'associated_distribution': 'Numpy Log-normal Distribution (random.lognormal)',
                    'parameters': {'mean_gaussian': -0.5742377578494785, 'standard_deviation_gaussian': 0.09373162411398223},
                },
                'exhalation_rate': {
                    'associated_distribution': 'Numpy Log-normal Distribution (random.lognormal)',
                    'parameters': {'mean_gaussian': -0.5742377578494785, 'standard_deviation_gaussian': 0.09373162411398223},
                },
            },
            'Light activity': {
                'inhalation_rate': {
                    'associated_distribution': 'Numpy Log-normal Distribution (random.lognormal)',
                    'parameters': {'mean_gaussian': 0.21380242785625422, 'standard_deviation_gaussian': 0.09435378091059601},
                },
                'exhalation_rate': {
                    'associated_distribution': 'Numpy Log-normal Distribution (random.lognormal)',
                    'parameters': {'mean_gaussian': 0.21380242785625422, 'standard_deviation_gaussian': 0.09435378091059601},
                },
            },
            'Moderate activity': {
                'inhalation_rate': {
                    'associated_distribution': 'Numpy Log-normal Distribution (random.lognormal)',
                    'parameters': {'mean_gaussian': 0.551771330362601, 'standard_deviation_gaussian': 0.1894616357138137},
                },
                'exhalation_rate': {
                    'associated_distribution': 'Numpy Log-normal Distribution (random.lognormal)',
                    'parameters': {'mean_gaussian': 0.551771330362601, 'standard_deviation_gaussian': 0.1894616357138137},
                },
            },
            'Heavy exercise': {
                'inhalation_rate': {
                    'associated_distribution': 'Numpy Log-normal Distribution (random.lognormal)',
                    'parameters': {'mean_gaussian': 1.1644665696723049, 'standard_deviation_gaussian': 0.21744554768657565},
                },
                'exhalation_rate': {
                    'associated_distribution': 'Numpy Log-normal Distribution (random.lognormal)',
                    'parameters': {'mean_gaussian': 1.1644665696723049, 'standard_deviation_gaussian': 0.21744554768657565},
                },
            },
        }
        self.symptomatic_vl_frequencies = {
            'log_variable': [2.46032, 2.67431, 2.85434, 3.06155, 3.25856, 3.47256, 3.66957, 3.85979, 4.09927, 4.27081,
                             4.47631, 4.66653, 4.87204, 5.10302, 5.27456, 5.46478, 5.6533, 5.88428, 6.07281, 6.30549,
                             6.48552, 6.64856, 6.85407, 7.10373, 7.30075, 7.47229, 7.66081, 7.85782, 8.05653, 8.27053,
                             8.48453, 8.65607, 8.90573, 9.06878, 9.27429, 9.473, 9.66152, 9.87552],
            'frequencies': [0.001206885, 0.007851618, 0.008078144, 0.01502491, 0.013258014, 0.018528495, 0.020053765,
                            0.021896167, 0.022047184, 0.018604005, 0.01547796, 0.018075445, 0.021503523, 0.022349217,
                            0.025097721, 0.032875078, 0.030594727, 0.032573045, 0.034717482, 0.034792991,
                            0.033267721, 0.042887485, 0.036846816, 0.03876473, 0.045016819, 0.040063473, 0.04883754,
                            0.043944602, 0.048142864, 0.041588741, 0.048762031, 0.027921732, 0.033871788,
                            0.022122693, 0.016927718, 0.008833228, 0.00478598, 0.002807662],
            'kernel_bandwidth': 0.1,
        }
        self.covid_overal_vl_data = {
            'shape_factor': 3.47,
            'scale_factor': 7.01,
            'start': 0.01,
            'stop': 0.99,
            'num': 30.0,
            'min_bound': 2,
            'max_bound': 10,
            'interpolation_fp_left': 0,
            'interpolation_fp_right': 0,
            'max_function': 0.2,
        }
        self.viable_to_RNA_ratio_distribution = {
            'low': 0.01,
            'high': 0.6,
        }
        self.infectious_dose_distribution = {
            'low': 10,
            'high': 100,
        }
        self.virus_distributions = {
            'SARS_CoV_2': {
                'viral_load_in_sputum': 'Ref: Viral load - covid_overal_vl_data',
                'infectious_dose': 'Ref: Infectious dose - infectious_dose_distribution',
                'viable_to_RNA_ratio': 'Ref: Viable to RNA ratio - viable_to_RNA_ratio_distribution',
                'transmissibility_factor': 1,
                'infectiousness_days': 14,
            },
            'SARS_CoV_2_ALPHA': {
                'viral_load_in_sputum': 'Ref: Viral load - covid_overal_vl_data',
                'infectious_dose': 'Ref: Infectious dose - infectious_dose_distribution',
                'viable_to_RNA_ratio': 'Ref: Viable to RNA ratio - viable_to_RNA_ratio_distribution',
                'transmissibility_factor': 0.78,
                'infectiousness_days': 14,
            },
            'SARS_CoV_2_BETA': {
                'viral_load_in_sputum': 'Ref: Viral load - covid_overal_vl_data',
                'infectious_dose': 'Ref: Infectious dose - infectious_dose_distribution',
                'viable_to_RNA_ratio': 'Ref: Viable to RNA ratio - viable_to_RNA_ratio_distribution',
                'transmissibility_factor': 0.8,
                'infectiousness_days': 14
            },
            'SARS_CoV_2_GAMMA': {
                'viral_load_in_sputum': 'Ref: Viral load - covid_overal_vl_data',
                'infectious_dose': 'Ref: Infectious dose - infectious_dose_distribution',
                'viable_to_RNA_ratio': 'Ref: Viable to RNA ratio - viable_to_RNA_ratio_distribution',
                'transmissibility_factor': 0.72,
                'infectiousness_days': 14
            },
            'SARS_CoV_2_DELTA': {
                'viral_load_in_sputum': 'Ref: Viral load - covid_overal_vl_data',
                'infectious_dose': 'Ref: Infectious dose - infectious_dose_distribution',
                'viable_to_RNA_ratio': 'Ref: Viable to RNA ratio - viable_to_RNA_ratio_distribution',
                'transmissibility_factor': 0.51,
                'infectiousness_days': 14
            },
            'SARS_CoV_2_OMICRON': {
                'viral_load_in_sputum': 'Ref: Viral load - covid_overal_vl_data',
                'infectious_dose': 'Ref: Infectious dose - infectious_dose_distribution',
                'viable_to_RNA_ratio': 'Ref: Viable to RNA ratio - viable_to_RNA_ratio_distribution',
                'transmissibility_factor': 0.2,
                'infectiousness_days': 14
            },
            'SARS_CoV_2_Other': {
                'viral_load_in_sputum': 'Ref: Viral load - covid_overal_vl_data',
                'infectious_dose': 'Ref: Infectious dose - infectious_dose_distribution',
                'viable_to_RNA_ratio': 'Ref: Viable to RNA ratio - viable_to_RNA_ratio_distribution',
                'transmissibility_factor': 0.1,
                'infectiousness_days': 14,
            },
        }
        self.mask_distributions = {
            'Type I': {
                'η_inhale': {
                    'associated_distribution': 'Numpy Uniform Distribution (random.uniform)',
                    'parameters': {
                        'low': 0.25,
                        'high': 0.80,
                    },
                },
                'Known filtration efficiency of masks when exhaling?': 'No',
                'factor_exhale': 1,
            },
            'FFP2': {
                'η_inhale': {
                    'associated_distribution': 'Numpy Uniform Distribution (random.uniform)',
                    'parameters': {
                        'low': 0.83,
                        'high': 0.91,
                    },
                },
                'Known filtration efficiency of masks when exhaling?': 'No',
                'factor_exhale': 1,
            },
            'Cloth': {
                'η_inhale': {
                    'associated_distribution': 'Numpy Uniform Distribution (random.uniform)',
                    'parameters': {
                        'low': 0.05,
                        'high': 0.40,
                    },
                },
                'Known filtration efficiency of masks when exhaling?': 'Yes',
                'η_exhale': {
                    'associated_distribution': 'Numpy Uniform Distribution (random.uniform)',
                    'parameters': {
                        'low': 0.20,
                        'high': 0.50,
                    },
                },
                'factor_exhale': 1,
            },
        }
        self.expiration_BLO_factors = {
            'Breathing': {'B': 1., 'L': 0., 'O': 0., },
            'Speaking': {'B': 1., 'L': 1., 'O': 1., },
            'Singing': {'B': 1., 'L': 5., 'O': 5., },
            'Shouting': {'B': 1., 'L': 5., 'O': 5., },
        }
        self.long_range_expiration_distributions = {
            'minimum_diameter': 0.1,
            'maximum_diameter': 30,
        }
        self.short_range_expiration_distributions = {
            'minimum_diameter': 0.1,
            'maximum_diameter': 100,
        }
        self.short_range_distances = {
            'minimum_distance': 0.5,
            'maximum_distance': 2.,
        }

        ####################################

        self.room = {
            'defaults': {
                'inside_temp': 293,
                'humidity_with_heating': 0.3,
                'humidity_without_heating': 0.5,
            },
        }
        self.ventilation = {
            'natural': {
                'discharge_factor': {
                    'sliding': 0.6,
                },
            },
            'infiltration_ventilation': 0.25,
        }
        self.particle = {
            'evaporation_factor': 0.3,
        }
        self.population_with_virus = {
            'fraction_of_infectious_virus': 1,
        }
        self.concentration_model = {
            'min_background_concentration': 0.,
            'CO2_concentration_model': {
                'CO2_atmosphere_concentration': 440.44,
                'CO2_fraction_exhaled': 0.042,
            },
        }
        self.short_range_model = {
            'dilution_factor': {
                'mouth_diameter': 0.02,
                'exhalation_coefficient': 2,
                'tstar': 2,
                'penetration_coefficients': {
                    '𝛽r1': 0.18, '𝛽r2': .2, '𝛽x1': 2.4,
                },
            },
        }
        self.exposure_model = {
            'repeats': 1,
        }
        self.conditional_prob_inf_given_viral_load = {
            'lower_percentile': 0.05,
            'upper_percentile': 0.95,
            'min_vl': 2,
            'max_vl': 10,
        }
        self.monte_carlo_sample_size = 250000
        self.population_scenario_activity = {
            'office': {'activity': 'Seated', 'expiration': {'Speaking': 1, 'Breathing': 2}},
            'smallmeeting': {'activity': 'Seated', 'expiration': {'Speaking': 1, 'Breathing': None}},
            'largemeeting': {'activity': 'Standing', 'expiration': {'Speaking': 1, 'Breathing': 2}},
            'callcenter': {'activity': 'Seated', 'expiration': {'Speaking': 1}},
            'controlroom-day': {'activity': 'Seated', 'expiration': {'Speaking': 1, 'Breathing': 1}},
            'controlroom-night': {'activity': 'Seated', 'expiration': {'Speaking': 1, 'Breathing': 9}},
            'library': {'activity': 'Seated', 'expiration': {'Breathing': 1}},
            'lab': {'activity': 'Light activity', 'expiration': {'Speaking': 1, 'Breathing': 1}},
            'workshop': {'activity': 'Moderate activity', 'expiration': {'Speaking': 1, 'Breathing': 1}},
            'training': {'activity': 'Standing', 'expiration': {'Speaking': 1}},
            'training_attendee': {'activity': 'Seated', 'expiration': {'Breathing': 1}},
            'gym': {'activity': 'Heavy exercise', 'expiration': {'Breathing': 1}},
            'household-day': {'activity': 'Light activity', 'expiration': {'Breathing': 5, 'Speaking': 5}},
            'household-night': {'activity': 'Seated', 'expiration': {'Breathing': 7, 'Speaking': 3}},
            'primary-school': {'activity': 'Light activity', 'expiration': {'Breathing': 5, 'Speaking': 5}},
            'secondary-school': {'activity': 'Light activity', 'expiration': {'Breathing': 7, 'Speaking': 3}},
            'university': {'activity': 'Seated', 'expiration': {'Breathing': 9, 'Speaking': 1}},
            'restaurant': {'activity': 'Seated', 'expiration': {'Breathing': 1, 'Speaking': 9}},
            'precise': {'activity': None, 'expiration': None},
        }

    async def populate_data(self):
        """
        Fetches data from the API and populates the configuration object.
        """
        if not self.data_fetched and os.environ.get('DATA_SERVICE_ENABLED', 'False').lower() == 'true':
            # Fetch and populate data from API
            await GlobalStore.populate_from_api()
            data = GlobalStore.get_data()['data']

            # Dynamically set attributes based on the data fetched from the API
            for attr_name, value in data.items():
                setattr(self, attr_name, value)

            self.data_fetched = True
        return


config = Configuration()

asyncio.run(config.populate_data())
