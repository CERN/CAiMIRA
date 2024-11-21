from ..models.enums import ViralLoads


class DataRegistry:
    """Registry to hold data values."""

    version = None

    expiration_particle = {
        "particle_size_range": {
            "long_range": {
                "minimum_diameter": 0.1,
                "maximum_diameter": 30,
                "references": "Morawska et al. (https://doi.org/10.1016/j.jaerosci.2008.11.002); Johnson et al. (https://doi.org/10.1016/j.jaerosci.2011.07.009).",
            },
            "short_range": {
                "minimum_diameter": 0.1,
                "maximum_diameter": 100,
                "references": "Morawska et al. (https://doi.org/10.1016/j.jaerosci.2008.11.002); Johnson et al. (https://doi.org/10.1016/j.jaerosci.2011.07.009).",
            },
        },   
        "BLOmodel": {
            "cn": {"B": 0.06, "L": 0.2, "O": 0.0010008},
            "mu": {"B": 0.989541, "L": 1.38629, "O": 4.97673},
            "sigma": {"B": 0.262364, "L": 0.506818, "O": 0.585005},
            "references": "Morawska et al. (https://doi.org/10.1016/j.jaerosci.2008.11.002); Johnson et al. (https://doi.org/10.1016/j.jaerosci.2011.07.009).",
        },
        "expiration_BLO_factors": {
            "Breathing": {"B": 1., "L": 0., "O": 0., },
            "Speaking": {"B": 1., "L": 1., "O": 1., },
            "Singing": {"B": 1., "L": 5., "O": 5., },
            "Shouting": {"B": 1., "L": 5., "O": 5., },
            "references": "Morawska et al. (https://doi.org/10.1016/j.jaerosci.2008.11.002); Johnson et al. (https://doi.org/10.1016/j.jaerosci.2011.07.009).",
        },
        "particle": {
            "evaporation_factor": 0.3,
            "references": "Marr et al. (https://doi.org/10.1098/rsif.2018.0298).",
        },
    }

    activity_distributions = {
        "Seated": {
            "inhalation_rate": {
                "associated_value": "Log-normal distribution",
                "parameters": {
                    "lognormal_mean_gaussian": -0.6872121723362303,
                    "lognormal_standard_deviation_gaussian": 0.10498338229297108,
                },
                "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
            },
            "exhalation_rate": {
                "associated_value": "Log-normal distribution",
                "parameters": {
                    "lognormal_mean_gaussian": -0.6872121723362303,
                    "lognormal_standard_deviation_gaussian": 0.10498338229297108,
                },
                "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
            },
        },
        "Standing": {
            "inhalation_rate": {
                "associated_value": "Log-normal distribution",
                "parameters": {
                    "lognormal_mean_gaussian": -0.5742377578494785,
                    "lognormal_standard_deviation_gaussian": 0.09373162411398223,
                },
                "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
            },
            "exhalation_rate": {
                "associated_value": "Log-normal distribution",
                "parameters": {
                    "lognormal_mean_gaussian": -0.5742377578494785,
                    "lognormal_standard_deviation_gaussian": 0.09373162411398223,
                },
                "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
            },
        },
        "Light activity": {
            "inhalation_rate": {
                "associated_value": "Log-normal distribution",
                "parameters": {
                    "lognormal_mean_gaussian": 0.21380242785625422,
                    "lognormal_standard_deviation_gaussian": 0.09435378091059601,
                },
                "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
            },
            "exhalation_rate": {
                "associated_value": "Log-normal distribution",
                "parameters": {
                    "lognormal_mean_gaussian": 0.21380242785625422,
                    "lognormal_standard_deviation_gaussian": 0.09435378091059601,
                },
                "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
            },
        },
        "Moderate activity": {
            "inhalation_rate": {
                "associated_value": "Log-normal distribution",
                "parameters": {
                    "lognormal_mean_gaussian": 0.551771330362601,
                    "lognormal_standard_deviation_gaussian": 0.1894616357138137,
                },
                "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
            },
            "exhalation_rate": {
                "associated_value": "Log-normal distribution",
                "parameters": {
                    "lognormal_mean_gaussian": 0.551771330362601,
                    "lognormal_standard_deviation_gaussian": 0.1894616357138137,
                },
                "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
            },
        },
        "Heavy exercise": {
            "inhalation_rate": {
                "associated_value": "Log-normal distribution",
                "parameters": {
                    "lognormal_mean_gaussian": 1.1644665696723049,
                    "lognormal_standard_deviation_gaussian": 0.21744554768657565,
                },
                "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
            },
            "exhalation_rate": {
                "associated_value": "Log-normal distribution",
                "parameters": {
                    "lognormal_mean_gaussian": 1.1644665696723049,
                    "lognormal_standard_deviation_gaussian": 0.21744554768657565,
                },
                "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
            },
        },
    }
    
    virological_data = {
        "symptomatic_vl_frequencies": {
            "associated_value": "Log Custom Kernel distribution",
            "parameters": {
                "log_variable": [
                    2.46032,
                    2.67431,
                    2.85434,
                    3.06155,
                    3.25856,
                    3.47256,
                    3.66957,
                    3.85979,
                    4.09927,
                    4.27081,
                    4.47631,
                    4.66653,
                    4.87204,
                    5.10302,
                    5.27456,
                    5.46478,
                    5.6533,
                    5.88428,
                    6.07281,
                    6.30549,
                    6.48552,
                    6.64856,
                    6.85407,
                    7.10373,
                    7.30075,
                    7.47229,
                    7.66081,
                    7.85782,
                    8.05653,
                    8.27053,
                    8.48453,
                    8.65607,
                    8.90573,
                    9.06878,
                    9.27429,
                    9.473,
                    9.66152,
                    9.87552,
                ],
                "frequencies": [
                    0.001206885,
                    0.007851618,
                    0.008078144,
                    0.01502491,
                    0.013258014,
                    0.018528495,
                    0.020053765,
                    0.021896167,
                    0.022047184,
                    0.018604005,
                    0.01547796,
                    0.018075445,
                    0.021503523,
                    0.022349217,
                    0.025097721,
                    0.032875078,
                    0.030594727,
                    0.032573045,
                    0.034717482,
                    0.034792991,
                    0.033267721,
                    0.042887485,
                    0.036846816,
                    0.03876473,
                    0.045016819,
                    0.040063473,
                    0.04883754,
                    0.043944602,
                    0.048142864,
                    0.041588741,
                    0.048762031,
                    0.027921732,
                    0.033871788,
                    0.022122693,
                    0.016927718,
                    0.008833228,
                    0.00478598,
                    0.002807662,
                ],
                "kernel_bandwidth": 0.1,
            },
            "references": "Henriques et al. (https://doi.org/10.1101/2021.10.14.21264988) and references therein.",
        },
        "covid_overal_vl_data": {
            "associated_value": "Weibull distribution",
            "parameters": {
                "shape_factor": 3.47,
                "scale_factor": 7.01,
                "start": 0.01,
                "stop": 0.99,
                "num": 30.0,
                "min_bound": 2,
                "max_bound": 10,
                "interpolation_fp_left": 0,
                "interpolation_fp_right": 0,
                "max_function": 0.2,
            },
            "references": "Chen et al. (https://elifesciences.org/articles/65774); First line of the figure in https://iiif.elifesciences.org/lax:65774%2Felife-65774-fig4-figsupp3-v2.tif/full/1500,/0/default.jpg.",
        },
        "virus_distributions": {
            "SARS_CoV_2": {
                "viral_load_in_sputum": ViralLoads.COVID_OVERALL.value,
                "infectious_dose": {
                    "associated_value": "Uniform distribution",
                    "parameters": {"low": 10, "high": 100},
                    "references": "Lednicky et al. (https://doi.org/10.1016/j.ijid.2020.09.025); Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
                },
                "viable_to_RNA_ratio": {
                    "associated_value": "Uniform distribution",
                    "parameters": {"low": 0.01, "high": 0.6},
                    "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
                },
                "transmissibility_factor": {
                    "value": 1,
                    "references": "Campbell et al. (https://doi.org/10.2807/1560-7917.ES.2021.26.24.2100509.)",
                },
                "infectiousness_days": {
                    "value": 14,
                    "references": "From French and Swiss guidelines (2021), supported by WHO (https://iris.who.int/bitstream/handle/10665/342004/WHO-2019-nCoV-IHR-Quarantine-2021.1-eng.pdf). Only used for incidence rate calculations.",
                },
            },
            "SARS_CoV_2_ALPHA": {
                "viral_load_in_sputum": ViralLoads.COVID_OVERALL.value,
                "infectious_dose": {
                    "associated_value": "Uniform distribution",
                    "parameters": {"low": 10, "high": 100},
                    "references": "Lednicky et al. (https://doi.org/10.1016/j.ijid.2020.09.025); Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
                },
                "viable_to_RNA_ratio": {
                    "associated_value": "Uniform distribution",
                    "parameters": {"low": 0.01, "high": 0.6},
                    "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
                },
                "transmissibility_factor": {
                    "value": 0.78,
                    "references": "Campbell et al. (https://doi.org/10.2807/1560-7917.ES.2021.26.24.2100509.)",
                },
                "infectiousness_days": {
                    "value": 14,
                    "references": "From French and Swiss guidelines (2021), supported by WHO (https://iris.who.int/bitstream/handle/10665/342004/WHO-2019-nCoV-IHR-Quarantine-2021.1-eng.pdf). Only used for incidence rate calculations.",
                },
            },
            "SARS_CoV_2_BETA": {
                "viral_load_in_sputum": ViralLoads.COVID_OVERALL.value,
                "infectious_dose": {
                    "associated_value": "Uniform distribution",
                    "parameters": {"low": 10, "high": 100},
                    "references": "Lednicky et al. (https://doi.org/10.1016/j.ijid.2020.09.025); Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
                },
                "viable_to_RNA_ratio": {
                    "associated_value": "Uniform distribution",
                    "parameters": {"low": 0.01, "high": 0.6},
                    "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
                },
                "transmissibility_factor": {
                    "value": 0.8,
                    "references": "Campbell et al. (https://doi.org/10.2807/1560-7917.ES.2021.26.24.2100509.)",
                },
                "infectiousness_days": {
                    "value": 14,
                    "references": "From French and Swiss guidelines (2021), supported by WHO (https://iris.who.int/bitstream/handle/10665/342004/WHO-2019-nCoV-IHR-Quarantine-2021.1-eng.pdf). Only used for incidence rate calculations.",
                },
            },
            "SARS_CoV_2_GAMMA": {
                "viral_load_in_sputum": ViralLoads.COVID_OVERALL.value,
                "infectious_dose": {
                    "associated_value": "Uniform distribution",
                    "parameters": {"low": 10, "high": 100},
                    "references": "Lednicky et al. (https://doi.org/10.1016/j.ijid.2020.09.025); Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
                },
                "viable_to_RNA_ratio": {
                    "associated_value": "Uniform distribution",
                    "parameters": {"low": 0.01, "high": 0.6},
                    "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
                },
                "transmissibility_factor": {
                    "value": 0.72,
                    "references": "Campbell et al. (https://doi.org/10.2807/1560-7917.ES.2021.26.24.2100509.)",
                },
                "infectiousness_days": {
                    "value": 14,
                    "references": "From French and Swiss guidelines (2021), supported by WHO (https://iris.who.int/bitstream/handle/10665/342004/WHO-2019-nCoV-IHR-Quarantine-2021.1-eng.pdf). Only used for incidence rate calculations.",
                },
            },
            "SARS_CoV_2_DELTA": {
                "viral_load_in_sputum": ViralLoads.COVID_OVERALL.value,
                "infectious_dose": {
                    "associated_value": "Uniform distribution",
                    "parameters": {"low": 10, "high": 100},
                    "references": "Lednicky et al. (https://doi.org/10.1016/j.ijid.2020.09.025); Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
                },
                "viable_to_RNA_ratio": {
                    "associated_value": "Uniform distribution",
                    "parameters": {"low": 0.01, "high": 0.6},
                    "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
                },
                "transmissibility_factor": {
                    "value": 0.51,
                    "references": "Campbell et al. (https://doi.org/10.2807/1560-7917.ES.2021.26.24.2100509.)",
                },
                "infectiousness_days": {
                    "value": 14,
                    "references": "From French and Swiss guidelines (2021), supported by WHO (https://iris.who.int/bitstream/handle/10665/342004/WHO-2019-nCoV-IHR-Quarantine-2021.1-eng.pdf). Only used for incidence rate calculations.",
                },
            },
            "SARS_CoV_2_OMICRON": {
                "viral_load_in_sputum": ViralLoads.COVID_OVERALL.value,
                "infectious_dose": {
                    "associated_value": "Uniform distribution",
                    "parameters": {"low": 10, "high": 100},
                    "references": "Lednicky et al. (https://doi.org/10.1016/j.ijid.2020.09.025); Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
                },
                "viable_to_RNA_ratio": {
                    "associated_value": "Uniform distribution",
                    "parameters": {"low": 0.01, "high": 0.6},
                    "references": "Henriques et al. (https://doi.org/10.1098/rsfs.2021.0076) and references therein.",
                },
                "transmissibility_factor": {
                    "value": 0.2,
                    "references": "Du et al. (https://www.mdpi.com/1999-4915/14/4/821).",
                },
                "infectiousness_days": {
                    "value": 14,
                    "references": "From French and Swiss guidelines (2021), supported by WHO (https://iris.who.int/bitstream/handle/10665/342004/WHO-2019-nCoV-IHR-Quarantine-2021.1-eng.pdf). Only used for incidence rate calculations.",
                },
            },
        },
    }

    mask_distributions = {
        "Type I": {
            "η_inhale": {
                "associated_value": "Uniform distribution",
                "parameters": {
                    "low": 0.25,
                    "high": 0.80,
                },
                "references": "Pan et al. (https://doi.org/10.1080/02786826.2021.1890687); Booth et al. (https://doi.org/10.1016/j.jhin.2013.02.007); Monn et al. (https://doi.org/10.4209/aaqr.2020.08.0531).",
            },
            "factor_exhale": {
                "value": 1,
                "references": "",
            },
        },
        "FFP2": {
            "η_inhale": {
                "associated_value": "Uniform distribution",
                "parameters": {
                    "low": 0.83,
                    "high": 0.91,
                },
                "references": "Pan et al. (https://doi.org/10.1080/02786826.2021.1890687); Booth et al. (https://doi.org/10.1016/j.jhin.2013.02.007); Monn et al. (https://doi.org/10.4209/aaqr.2020.08.0531).",
            },
            "factor_exhale": {
                "value": 1,
                "references": "",
            },
        },
        "Cloth": {
            "η_inhale": {
                "associated_value": "Uniform distribution",
                "parameters": {
                    "low": 0.05,
                    "high": 0.40,
                },
                "references": "Pan et al. (https://doi.org/10.1080/02786826.2021.1890687); Booth et al. (https://doi.org/10.1016/j.jhin.2013.02.007); Monn et al. (https://doi.org/10.4209/aaqr.2020.08.0531).",
            },
            "η_exhale": {
                "associated_value": "Uniform distribution",
                "parameters": {
                    "low": 0.20,
                    "high": 0.50,
                },
                "references": "Pan et al. (https://doi.org/10.1080/02786826.2021.1890687); Booth et al. (https://doi.org/10.1016/j.jhin.2013.02.007); Monn et al. (https://doi.org/10.4209/aaqr.2020.08.0531).",
            },
            "factor_exhale": {
                "value": 1,
                "references": "",
            },
        },
    }

    ####################################

    room = {
        "inside_temp": 293.,
        "humidity_with_heating": 0.3,
        "humidity_without_heating": 0.5,
        "references": "N/A.",
    }

    ventilation = {
        "natural": {
            "discharge_factor": {
                "sliding": 0.6,
            },
        },
        "infiltration_ventilation": 0.25,
        "references": "Henriques et al. (https://doi.org/10.1101/2021.10.14.21264988).",
    }

    concentration_model = {
        "virus_concentration_model": {
            "min_background_concentration": 0.0,
            "references": "N/A.",
        },
        "CO2_concentration_model": {
            "CO2_atmosphere_concentration": 440.44,
            "CO2_fraction_exhaled": 0.042,
            "references": "ECMWF - https://charts.ecmwf.int/products/carbon-dioxide-forecasts; Zhang et al. (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7127751/).",
        },
    }

    short_range_model = {
        "dilution_factor": {
            "mouth_diameter": 0.02,
            "exhalation_coefficient": 2,
            "breathing_cycle": 4,
            "penetration_coefficients": {
                "𝛽r1": 0.18,
                "𝛽r2": 0.2,
                "𝛽x1": 2.4,
            },
            "references": "Jia et al. (https://doi.org/10.1016/j.buildenv.2022.109166).",
        },
        "conversational_distance": {
            "minimum_distance": 0.5,
            "maximum_distance": 2.0,
            "references": "Derived from Fig. 8 a) 'stand-stand' in Zhang et al. (https://www.mdpi.com/1660-4601/17/4/1445).",
        },
    }

    monte_carlo = {
        "sample_size": 250000,
        "references": "N/A.",
    }

    population_scenario_activity = {
        "office": {"placeholder": "Office", "activity": "Seated", "expiration": {"Speaking": 1, "Breathing": 2}, "references": "N/A."},
        "smallmeeting": {
            "placeholder": "Small meeting (<10 occ.)",
            "activity": "Seated",
            "expiration": {"Speaking": 1},
            "references": "N/A.",
        },
        "largemeeting": {
            "placeholder": "Large meeting (>= 10 occ.)",
            "activity": "Standing",
            "expiration": {"Speaking": 1, "Breathing": 2},
            "references": "N/A.",
        },
        "callcenter": {"placeholder": "Call Center", "activity": "Seated", "expiration": {"Speaking": 1}},
        "controlroom-day": {
            "placeholder": "Control Room - Day shift",
            "activity": "Seated",
            "expiration": {"Speaking": 1, "Breathing": 1},
            "references": "N/A.",
        },
        "controlroom-night": {
            "placeholder": "Control Room - Night shift",
            "activity": "Seated",
            "expiration": {"Speaking": 1, "Breathing": 9},
            "references": "N/A.",
        },
        "library": {"placeholder": "Library", "activity": "Seated", "expiration": {"Breathing": 1}, "references": "N/A."},
        "lab": {
            "placeholder": "Lab",
            "activity": "Light activity",
            "expiration": {"Speaking": 1, "Breathing": 1},
            "references": "N/A.",
        },
        "workshop": {
            "placeholder": "Workshop",
            "activity": "Moderate activity",
            "expiration": {"Speaking": 1, "Breathing": 1},
            "references": "N/A.",
        },
        "training": {"placeholder": "Conference/Training (speaker infected)", "activity": "Standing", "expiration": {"Speaking": 1}, "references": "N/A."},
        "training_attendee": {"placeholder": "Conference/Training (attendee infected)", "activity": "Seated", "expiration": {"Breathing": 1}, "references": "N/A."},
        "gym": {"placeholder": "Gym", "activity": "Heavy exercise", "expiration": {"Breathing": 1}, "references": "N/A."},
        "household-day": {
            "placeholder": "Household (day time)",
            "activity": "Light activity",
            "expiration": {"Breathing": 5, "Speaking": 5},
            "references": "N/A.",
        },
        "household-night": {
            "placeholder": "Household (evening and night time)",
            "activity": "Seated",
            "expiration": {"Breathing": 7, "Speaking": 3},
            "references": "N/A."
        },
        "primary-school": {
            "placeholder": "Primary school",
            "activity": "Light activity",
            "expiration": {"Breathing": 5, "Speaking": 5},
            "references": "N/A.",
        },
        "secondary-school": {
            "placeholder": "Secondary school",
            "activity": "Light activity",
            "expiration": {"Breathing": 7, "Speaking": 3},
            "references": "N/A.",
        },
        "university": {
            "placeholder": "University",
            "activity": "Seated",
            "expiration": {"Breathing": 9, "Speaking": 1},
            "references": "N/A.",
        },
        "restaurant": {
            "placeholder": "Restaurant",
            "activity": "Seated",
            "expiration": {"Breathing": 1, "Speaking": 9},
            "references": "N/A.",
        },
        "precise": {"placeholder": "Precise", "activity": "", "expiration": {}, "references": "N/A."},
    }

    def to_dict(self):
        # Filter out methods, special attributes, and non-serializable objects
        data_dict = {
            key: value
            for key, value in self.__class__.__dict__.items()
            if not key.startswith("__") and not callable(value) and not isinstance(value, (type, classmethod, staticmethod))
        }
        return data_dict

    def update(self, data, version=None):
        """Update local cache with data provided as argument."""
        for attr_name, value in data.items():
            setattr(self, attr_name, value)

        if version:
            self.version = version
