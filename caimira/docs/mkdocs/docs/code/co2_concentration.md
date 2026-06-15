# Computation of the CO<sub>2</sub> Concentration


The estimate of the concentration of CO<sub>2</sub> in a given room to indicate the air quality is given by the same approach as for the long-range virus concentration,
$C_{\mathrm{LR}}(t, D)$, where $C_{\mathrm{LR},0}(D)$ is considered to be the background (outdoor) CO<sub>2</sub> concentration (`models.CO2ConcentrationModel.CO2_atmosphere_concentration()`).

In order to compute the CO<sub>2</sub> concentration one should then simply use the `models.CO2ConcentrationModel.concentration()` method.
A fraction of 4.2% of the exhalation rate of the defined activity was considered as supplied to the room (`models.CO2ConcentrationModel.CO2_fraction_exhaled()`).

Note still that nothing depends on the aerosol diameter $D$ in this case (no particles are involved) - hence in this class all parameters are constant w.r.t $D$.

Since the CO<sub>2</sub> concentration differs from the virus concentration, the specific removal rate, CO<sub>2</sub> atmospheric concentration and normalization factors are respectively defined in `models.CO2ConcentrationModel.removal_rate()`,
`models.CO2ConcentrationModel.min_background_concentration()` and `models.CO2ConcentrationModel.normalization_factor()`.