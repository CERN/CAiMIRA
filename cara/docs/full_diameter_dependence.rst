*****************************
Full diameter-dependent model
*****************************

Context
=======


The :mod:`cara.apps.calculator.model_generator` module is responsible to bind all the inputs defined in the user interface into the respective model variables.
The :py:mod:`cara.apps.calculator.report_generator` module is responsible to bind the results from the model calculations into the respective output variables presented in the CARA report.
The :mod:`cara.models` module itself implements the core CARA methods.  A useful feature of the implementation is that we can benefit from vectorization, which allows running multiple parameterization of the model at the same time.

Unlike other similar models, some of the CARA variables are considered for a given aerosol diameter **D**, 
as the behavior of the virus-laden particles in the room environment and inside the susceptible host (once inhaled) are diameter-dependent. 
These variables are identified by **(D)** in the variable name, such as the **emission rate** -- **vR(D)**, **removal rate** -- **vRR(D)**, and **concentration** -- **C(t, D)**.

Despite the outcome of the CARA results include the entire range of diameters, throughout the model,
most of the variables and parameters are kept in their diameter-dependent form for any possible detailed analysis of intermediate results.
Only the final quantities shown in output, such as the concentration and the dose, are integrated over the diameter distribution.
This is performed thanks to a Monte-Carlo integration at the level of the dose (vD\ :sup:`total`\) which is computed over a distribution of particle diameters,
from which the average value is then calculated -- this is equivalent to an analytical integral over diameters
provided the sample size is large enough.

It is important to distinguish between 1) Monte-Carlo random variables (which are vectorised independently on its diameter-dependence) and 2) numerical Monte-Carlo integration for the diameter-dependence
Since the integral of the diameter-dependent variables are solved when computing the dose -- vD\ :sup:`total`\ -- while performing some of the intermediate calculations, 
we normalize the results by *dividing* by the Monte-Carlo variables that are diameter-independent, so that they are not considered in the Monte-Carlo integration (e.g. :meth:`cara.models.ConcentrationModel.normed_integrated_concentration`).

Expiration
==========

In the **Expiration** class (representing the expiration of aerosols by an infected person) has , as one of its properties `Particle`, :attr:`cara.models.Expiration.particle`, 
which represents the virus-laden aerosol with a vectorised parameter: the particle `diameter` (assuming a perfect sphere).
For a given aerosol diameter, one :class:`cara.models.Expiration` object provides the aerosol **volume - Vp(D)**, multiplied by the **mask outward efficiency - ηout(D)** to include the filteration capacity, when applicable.

The BLO model represents the distribution of diameters used in the model. It corresponds to the sum of three lognormal distributions, weighted by the **B**, **L** and **O** modes.
The aerosol diameter distributions are given by the :meth:`cara.monte_carlo.data.BLOmodel.distribution` method.

The :class:`cara.monte_carlo.data.BLOmodel` class itself contains the method to return the mathematical values of the probability distribution for a given diameter (in microns), 
as well as the method to return the limits of integration between the **min** and **max** diameters.
The BLO model is used to provide the probability density function (PDF) of the aerosol diameters for a given **Expiration** type defined in :meth:`cara.monte_carlo.data.expiration_distribution`.
To compute the total number concentration of particles per mode (B, L and O), **cn** in particles/cm\ :sup:`3`\, in other words, the total concentration of aerosols per unit volume of expired air, 
an integration of the lognormal distributions is performed over all aerosol diameters. In the code it is used as a scaling factor in the :class:`cara.models.Expiration` class.

Under the :mod:`cara.apps.calculator.model_generator`, when it comes to generate the Expiration model, the `diameter` property is sampled through the BLO :meth:`cara.monte_carlo.data.BLOmodel.distribution` method, while the value for the **cn** is given by the :meth:`cara.monte_carlo.data.BLOmodel.integrate` method.
To summarize, the Expiration contains the distribution of the diameters as a vectorised float. Depending on different expiratory types, the contributions from each mode will be different, therefore the result in the distribution also differs from model to model.

Emission Rate - vR(D)
=====================

The mathematical equations to calculate vR(D) are defined in the paper
(Henriques A et al, Modelling airborne transmission of SARS-CoV-2 using CARA: risk assessment for enclosed spaces.
Interface Focus 20210076, https://doi.org/10.1098/rsfs.2021.0076) as follows:

:math:`vR(D)_j=vl_{in} . E_{c, j}(D, f_{amp}, η_{out}(D)) . BR_k` ,

:math:`E_{c, j}^{total}=\int_0^{D_{\mathrm{max}}} E_{c,j}(D)\, \mathrm{d}D` .

The later integral, which is giving the total emission rate, is calculated using a Monte-Carlo sampling of the particle diameters which follow the distribution given by **Np(D)**, which contains the scaling factor **cn**.

In the code, given an Expiration, we have different methods that perfom part of the calculations:

* Calculate the emission rate per aerosol, which is the multiplication of the diameter-independent variables: :meth:`cara.models.InfectedPopulation.emission_rate_per_aerosol_when_present`. It corresponds to :math:`vl_{in} . BR_{k}` part.
* Calculate the aerosols, which is the result of :math:`E_{c,j}(D) = Np(D) . Vp(D) . (1 − ηout(D))`: :meth:`cara.models.InfectedPopulation.aerosols`. Note that this result is not integrated over the diameters at this stage.
* Calculate the full emission rate, which is the multiplication of the two previous methods, and corresponds to the :math:`E_{c,j}(D)`: :meth:`cara.models._PopulationWithVirus.emission_rate_when_present`

Note that in the model the integral over the diameters is not realized at this stage, but rather when computing the dose, since other parameters also depend on **diameter** (D).
In order to perform the Monte-Carlo integration at this stage, the final result of the calculation should be averaged.

Long-range approach
===================

Concentration - C(t, D)
***********************

Starting with the long-range concentration of virus, that depends on the **emission rate**, the concentration of viruses in aerosols of a given size **D** is:

:math:`C(t, D)=\frac{\mathrm{vR}(D) \cdot N_{\mathrm{inf}}}{\lambda_{\mathrm{vRR}}(D) \cdot V_r}-\left (\frac{\mathrm{vR}(D) \cdot N_{\mathrm{inf}}}{\lambda_{\mathrm{vRR}}(D) \cdot V_r}-C_0(D) \right )e^{-\lambda_{\mathrm{vRR}}(D)t}` ,

where **emission rate vR(D)** and :math:`\lambda_{\mathrm{vRR}}` **(viral removal rate)** depend on the particle diameter **D**.
Since the emission rate is dependent on diameter-independent variables (:math:`vl_{in}` and :math:`BR_k``) that should not be included when calculating the integral, the concentration method was written to be normalized by the emission rate.

In other words, we can split the concentration in two different formulations:

* Normed concentration : :math:`CN(t, D)` that calculates the concentration without the multiplication by the emission rate.
* Concentration: :math:`C(t, D) = [CN(t, D) * vR(D)] * BR_k * vl_{in}`, where :math:`vR(D)` is the result of the :meth:`cara.models.Expiration.aerosols` method, while :math:`BR_k` and :math:`vl_{in}` are the diameter-independent Monte-Carlo variables.

This way, to calculate the concentration in the model, there are different methods that consider the normalization by the emission rate:

* **_normed_concentration**, that calculates the virus long-range exposure concentration, as function of time, and normalized by the emission rate. It corresponds to the previously mentioned :math:`CN(t, D)`.
* :meth:`cara.models.ConcentrationModel.concentration`, which calculates the virus long-range exposure concentration of viruses as function of time and diameter (:math:`C(t, D)` above). Note that in order to get the total concentration value in this stage, the final result should be averaged (this is equivalent to a Monte-Carlo integration over diameters, see above). In the calculator, the integral over the diameters is performed only when doing the concentration plot. Otherwise, it is done only at a later stage, when calculating the dose (in :class:`cara.models.ExposureModel`).

These two methods are used to calculate the concentration at a given time. At this stage to perform the integral over the diameters the resulting value should be averaged according to the Monte-Carlo integration.

The following methods calculate the integrated concentration between any two times. They are mostly used when calculating the **Dose**:

* :meth:`cara.models.ConcentrationModel.normed_integrated_concentration`, normed_integrated_concentration that returns the integrated long-range concentration of viruses in the air, between any two times, normalized by the emission rate. Note that this method performs the integral between any two times of the previously mentioned **_normed_concentration** method.
* :meth:`cara.models.ConcentrationModel.integrated_concentration`, that returns the same result as the previous one, but multiplied by the emission rate.

.. Note that the integral over the diameters is performed later in the dose, with the average of the samples, since the diameters are sampled according to the distribution given by **Np(D)**. The integral over different times is calculated directly in the class (integrated methods).

Dose - vD
*********

The term “dose” refers to the number of viable virions that will contribute to a potential infection.

The receiving dose, which is inhaled by the exposed host, in infectious virions per unit diameter, is calculated by first integrating the viral concentration profile (for a given particle diameter) over the exposure time and multiplying by a scaling factor to determine the proportion of virions which are infectious:

:math:`\mathrm{vD}(D)=\int_{t1}^{t2}C(t, D)\;dt \cdot f_{\mathrm{inf}} \cdot \mathrm{BR}_{\mathrm{k}} \cdot f_{\mathrm{dep}}(D) \cdot   (1-\eta_{\mathrm{in}})` .

Given that the calculation is diameter-dependent, to calculate the dose in the model, the code contains different methods that consider the parameters that are dependent on the aerosol size, **D**.
The total dose results from the sum of all the doses accumulated for each particle size is

:math:`\mathrm{vD^{total}} = \int_0^{D_{\mathrm{max}}} \mathrm{vD}(D) \, \mathrm{d}D` .

This calculation is computed using a Monte-Carlo integration. As previously described, many different parameters samples are generated using the probability distribution from the **Np(D)** equation.
The dose for each of them is then computed, and their **average** value over all samples represents a good approximation of the total dose, provided that the number of samples is large enough.

Regarding the first parameter, i.e. the concentration integrated over the time, the respective method is the :meth:`cara.models.ExposureModel._long_range_normed_exposure_between_bounds`, which calculates the long-range exposure (concentration) between two bounds (time1 and time2), normalized by the emission rate of the infected population.
This method filters out the given bounds considering the breaks through the day (i.e. the time intervals during which there is no exposition to the virus) and calls :meth:`cara.models.ConcentrationModel.normed_integrated_concentration` that gets the integrated long-range concentration of viruses in the air between any two times.
It corresponds to the :math:`\int_{t1}^{t2}C(t, D)\;dt` integral, normalized by the emission rate of the infected population.

After the calculations of the integrated concentration over the time, in order to calculate the final dose, we have to compute the remaining factors in the above equation.
Note that the Monte-Carlo integration is performed at this stage, where all the parameters that are diameter-dependent are grouped together to calculate the final average.
In other words, in the code the procedure is the following:

:math:`\mathrm{vD_{normed}} = (\int_{t1}^{t2}C(t, D)\;dt \cdot V_{aerosol}(D, mask) \cdot f_{\mathrm{dep}}(D)).mean()` .

The aerosol volume :math:`V_{aerosol}` is introduced because the integrated concentration over the time was previously normalized by the emission rate.
Here, to calculate the integral over the diameters we also need to consider the diameter-dependent variables that are on the emission rate, represented by the aerosol volume which depends on the diameter and on the mask type:

:math:`V_{aerosol}(D, mask) = \mathrm{cn} \cdot Vp(D) \cdot (1 − ηout(D))` .

The :math:`\mathrm{cn}` factor, which represents the total number of aerosols emitted, is introduced here as a scaling factor, as otherwise the Monte-Carlo integral would be normalized to 1 as the probability distribution.

Finally we multiply the result by all the remaining diameter-independent variables:

:math:`\mathrm{vD^{total}} = \mathrm{vD_{normed}} \cdot f_{inf} \cdot \mathrm{BR}_{k} \cdot (1 - η_{in}) \cdot \mathrm{vR_{ND}}` ,

with :math:`\mathrm{vR_{ND}} =` `emission_rate_per_aerosol` :math:`= vl_{in} \cdot \mathrm{BR}_{k}` .

The `emission_rate_per_aerosol` is introduced because of the previous normalization by the emission rate, except for the diameter-dependent variable :math:`V_{aerosol}` which was already in :math:`\mathrm{vD_{normed}}`. So one should multiply by the missing parameters :math:`vl_{in}` and :math:`BR_{k}` (see :meth:`cara.models.InfectedPopulation.emission_rate_per_aerosol_when_present`).

In the end, the dose is a vectorized float used in the probability of infection formula.

Short-range approach
====================

The short-range data class models a close-range interaction **concentration** and the respective **dilution_factor**.
Its properties are the **expiration** definition, the **activity type**, the **presence time**, and the **interpersonal distance** between any two individuals.
When generating a full model, the short-range class is defined with a new **Expiration** distribution, given that the **min** and **max** diameters for the short-range interations are different from those used in the long-range concentration (the idea is that very large particles should not be considered in the long-range case as they fall rapidly on the floor, while they must be in for the short-range case).

To calculate the short-range concentration, we first need to calculate what is the **concentration at the jet origin**, that depends on the diameter **D**. Very similar to what we did with the **emission rate**, we need to calculate the scaling factor from the probability distribution, **Np(D)**, as well as the **volume** for those diameters.

In the code, :meth:`cara.models.Expiration.jet_origin_concentration` computes the same quatity as :meth:`cara.models.Expiration.aerosols`, except for the mask inclusion. As previously mentioned, it is normalized by the **viral load**, which is a diameter-independent property.

When calculating the dose, we get the concentration normalized by the **viral load** and **breathing rate**, and without the **dilution factor**, since these parameters are Monte-Carlo variables that do not depend on the diameter.

Concentration - C(t, D)
***********************

The short-range concentration close to the mouth or nose of an exposed person, may be written as:

:math:`C_{SR}(t, D) = \frac{1}{S({x})}*(C_{0, SR}(D) - C(t, D))` .

It depends on the **long-range concentration** of viruses, on the **dilution factor** and on the **initial concentration** of viruses on the mouth or nose of the emitter.
As for the long-range concentration, we must normalize the short-range concentration on parameters that are diameter-dependent variables, to profit from the Monte-Carlo integration.
Besides that, one should consider that for each interaction, the expiration type may be different, therefore a new distribution of diameters should be taken into consideration.

The method to calculate the concentration viruses on the mouth or nose of the emitting person, has the viral load as multiplying factor:

:math:`C_{0, SR}=(\int_{D_{min}}^{D_{\mathrm{max = 1000μm}}} N_p(D) \cdot V_p(D)\, \mathrm{d}D) \cdot 10^{-6} \cdot vl_{in}` .

In other words, in the code we have one method that returns the value of :math:`N_p(D) \cdot V_p(D)`, :meth:`cara.models.Expiration.jet_origin_concentration`. Note that similarly to the `long-range` approach, the integral over the diameters is not calculated at this stage.

To calculate the `long-range` concentration of viruses, `C(t, D)`, we profit from the :meth:`cara.models.ConcentrationModel.long_range_normed_concentration` method, normalized by the viral load, the diameter-independent variable in the concentration.
However, since the diameter distribution is different on the `short-range` interactions, we need to perform one approximation using interpolation. The set of points we want the interpolated values are the short-range particle diameters (given by the current expiration). The set of points with a known value are the long-range particle diameters (given by the initial expiration). The set of known values are the long-range concentration values normalised by the viral load. At this point, we have a procedure to calculate :math:`C_{0, SR}  - C(t, D)`. Given that we already have the result of the `dilution_factor`, the result of :math:`\frac{1}{S({x})} \cdot (C_{0, SR}  - C(t, D))` is given by the method :meth:`cara.models.ShortRangeModel.normed_concentration`. To sum up, this method calculates the virus `short-range` exposure concentration, as a function of time. It is normalized by the viral load, and the integral over the diameters is not performed at this stage.

The method :meth:`cara.models.ShortRangeModel.short_range_concentration` applies the multiplication by the viral load to the result of the previous method, returning the final short-range concentration for a given time.

The final concentration is the sum of the `short-range` and `long-range` concentrations.

Dose - vD
*********

In theory, the `short-range` dose is defined as follows:

:math:`\mathrm{vD}(D)= \mathrm{vD^{long-range}}(D) + \sum\limits_{i=1}^{n} \int_{t1}^{t2}C_{SR}(t, D)\;dt \cdot f_{\mathrm{inf}} \cdot \mathrm{BR}_{\mathrm{k}} \cdot f_{\mathrm{dep}}(D) \cdot (1-\eta_{\mathrm{in}})` ,

where :math:`\mathrm{vD^{long-range}}(D)` is the long-range, diameter-dependent dose computed previously, and

:math:`\mathrm{vD^{total}} = \int_0^{D_{\mathrm{max}}} \mathrm{vD}(D) \, \mathrm{d}D` .

In the code, the method that returns the value for the dose is the :meth:`cara.models.ExposureModel.deposited_exposure_between_bounds`. First we perform the multiplications by the diameter-dependent variables so that we can profit from the Monte-Carlo integration. Then we multiply the final value by the diameter-independent variables.

The method :meth:`cara.models.ShortRangeModel.normed_jet_exposure_between_bounds` gets the integrated short-range concentration of viruses in the air between the times start and stop, normalized by the virus **viral load**, and without **dilution**. Very similar to the long-range procedure, this method performs the integral of the concentration for the given time boundaries.

Once we have the integral of the concentration normalized by the **viral load**, we multiply by the remaining diameter-dependent properties to perform the integral over the particle diameters, including the **fraction deposited** computed with an evaporation factor of `1` (as the aerosols do not have time to evaporate during a short-range interaction):

:math:`\int_{0}^{D_{max}}C_{SR}(t, D) \cdot f_{dep}(D) \;dD` .

Note that in the code we perform the subtraction between the concentration at the jet origin and the `long-range` concentration of viruses in two steps when we calculate the dose, since the contribution of the diameter-dependent variable :math:`f_{dep}` has to be multiplied separately in substractions:

`integral_over_diameters =` :math:`((C_{0, SR} \cdot f_{dep}) - (C(t, D) \cdot f_{dep})).mean()` .

To perform the integral, we calculate the average since it is a good approximation of the **vD** total, provided that the number of samples is large enough.

Then, we add the contribution to the result of the diameter-independent vectorized properties, which are the **dilution factor**, **viral load**, **fraction of infectious virus** and **breathing rate**:

`vD = integral_over_diameters . exhalation_rate . inhalation_rate / dilution` :math:`\cdot f_{inf} \cdot vl_{in} \cdot (1 - η_{in})` .

Note that the multiplication over the `exhalation_rate` is done at each `short-range` interaction since the `Activity` type may be different for different interactions.

The final dose is the sum of the `short-range` and `long-range` doses.
