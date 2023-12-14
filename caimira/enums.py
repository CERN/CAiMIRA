from enum import Enum

class ViralLoads(Enum):
    COVID_OVERALL = "Ref: Viral load - covid_overal_vl_data"
    SYMPTOMATIC_FREQUENCIES = "Ref: Viral load - symptomatic_vl_frequencies"


class InfectiousDoses(Enum):
    DISTRIBUTION  = "Ref: Infectious dose - infectious_dose_distribution"


class ViableToRNARatios(Enum):
    DISTRIBUTION  = "Ref: Viable to RNA ratio - viable_to_RNA_ratio_distribution"
