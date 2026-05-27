# Physics of the Model

The CAiMIRA model mimics the physical process of viral transmission through five stages presented in the topmost part of Figure 1: 
Emission, removal, concentration, dose, and infection probability. 
Along with viral transmission, CAiMIRA also simulates emission, removal, and concentration of CO_2, as shown in the lower part of Figure 1.
[![CAiMIRA Structure](CAiMIRA_structure.png)](CAiMIRA_structure.png)
*Figure 1: Structure of the CAiMIRA model showing the viral transmission and CO_2 simulation processes.*

The viral **emission rate** – $\mathrm{vR}(D)$, **removal rate** – $\mathrm{vRR}(D)$, **concentration** – $C(t, D)$, and **dose** $\mathrm{vD(D)}$ are considered for a given aerosol diameter $D$,
as the behavior of the virus-laden particles in the room environment and inside the respiratory tract are diameter-dependent. The probability of infection is computed from the total viral dose deposited in the respiratory tract

$\mathrm{vD^{total}} =\int_{\mathrm{D_{min}}}^{\mathrm{D_{max}}} \mathrm{vD(D)} \mathrm{d}D$

which is estimated by Monte Carlo integration (see below). 
For computational efficiency, the diameter-dependent dose $\mathrm{vD(D)}$ is factored into three components: 
A probability distribution of $D$, a diameter-independent component, and a remaining diameter-dependent component. 
Because the viral concentration is a factor of the dose, and the viral emission rate is a factor of the viral concentration, $C(t, D)$ and $\mathrm{vR}(D)$ are also factored into probability distribution of $D$, a diameter-independent component, and a remaining diameter-dependent component (details below).
Intermediate results for the total viral emission rate $\mathrm{vR}^{total}$, total viral removal rate $\mathrm{vRR}^{total}$, and total viral concentration $\mathrm{C(t)}^{total}$ can also be obtained by integrating over the particle diameter.

This page describes the derivation of the equations specifying the emission rate, removal rate, and concentration of virions and CO_2, as well as the viral dose exposure and probability of infection (see Figure 1). 
After having derived the full equations, it is described how the computations are devided into different classes and methods in the CAiMIRA implementation for computational efficiency.

## Backend Structure

The `caimira.calculator.validators` package contains modules responsible for binding all input values from the request to their respective model variables. These modules, `co2.co2_validator` and `virus.virus_validator`, inherit from the parent `form_validator` module, and handle input validation for the CO<sub>2</sub> and virus model generators, respectively.
The `caimira.calculator.report` package contains modules responsible for binding all results from the model calculations into the respective output variables in the request output. These modules, `co2_report_data` and `virus_report_data`, handle outputs for the CO<sub>2</sub> and virus model, respectively.
The `caimira.calculator.store.data_registry` contains input values to CAiMIRA that are not user-defined. These are collected in a class **DataRegistry**.
The `caimira.calculator.models.models` module itself implements the core CAiMIRA methods. A useful feature of the implementation is that we can benefit from vectorization, which allows running multiple parameterizations of the model at the same time.


## Emission 
### Derivation of the Analytical Emission Rate
Infectious individuals inside the room are assumed to be the only source of virus. Their emission rate per unit diameter of infectious virus is

$\mathrm{vR}(D)= {\mathrm{BR}}_{\mathrm{k}} \cdot \mathrm{vl_{in}} \cdot f_{\mathrm{inf}} \cdot E_c(D)$

given the breathing rate ${\mathrm{BR}}_{\mathrm{k}}$ for a constant physical activity $k \in \{\mathrm{Seated}, \mathrm{Standing}, \mathrm{Light},$ $\mathrm{Moderate}, \mathrm{Heavy}\}$. $vl_{\mathrm{in}}$ is the viral load in the respiratory tract (in RNA copies per mL) and $f_{inf}$ is the fraction of infectious virus. 
$E_c(D)$ represents the volumetric particle emission concentration per unit diameter (in mL/(m<sub>3</sub> .µm) given by

$E_{c}(D) = N_p(D) \cdot V_p(D) \cdot (1 − η_\mathrm{out}(D))$

where $V_p(D)$ is the particles' individual volume and $\eta_{out}$ is the outward mask efficiency. For an expiratory activity $j \subseteq \{\mathrm{Breathing}, \mathrm{Speaking}, \mathrm{Singing}, \mathrm{Shouting}\}$, the number of particles with diameter $D$ is given by 

$N_{p}(D)=\sum_{\forall j} \sum_{i \in \{\mathrm{B},\mathrm{L},\mathrm{O}\}} a_j \cdot f_{\mathrm{amp}, j, i} \cdot c_{n,i} \cdot \left[\frac{1}{D\sqrt{2 \pi} \sigma_{D_i}} \exp{-\frac{(\ln D -\mu_{D_i})^2}{2 (\sigma_{D_i})^2}}\right]$

for B = bronchial, L = larynx, O = oral being the sources of the emitted particles. $a_j$ is the fraction of time the infected performes each expiratory activity $j$.
$c_{n,i}$ is the particle emission concentration, and $\mu_{D_i}$ and $\sigma_{D_i}$ are the mean and standard deviations, respectively, of the log-normal distribution found to fit the number of expired particles with diameter $D$, for $i \in \{\mathrm{B},\mathrm{L},\mathrm{O}\}$ \citep{BLOfit}. 
$f_{\mathrm{amp}, j, i}$ is the amplitude of the vocalization, set to 5 for $i \in \{L,O\}$ if $j = \{\text{Singing}, \text{Shouting}\}$ and otherwise 1. Note, however, that for $i \in \{L,O\}$ and $j = \text{Breathing}$ $f_{\mathrm{amp}, j, i}$ is set to zero in `caimira.calculator.store.data_registry`, although it is technically the particle emission concentration $c_{n,i}$ that is zero in that case. This technicallity has no effect on the output, it only simplifies the implementation of $c_{n,i}$.

Note that the diameter-dependence is kept at this stage. Since other parameters downstream in code are also diameter-dependent, the Monte-Carlo integration over the particle diameter is computed at the level of the dose $\mathrm{vD^{total}}$.
In case one would like to have intermediate results for emission rate, however, one may compute

$\mathrm{vR}^{total} = \int_{D_{\mathrm{min}}}^{D_{\mathrm{max}}} {\mathrm{BR}}_{\mathrm{k}} \cdot \mathrm{vl_{in}} \cdot f_{\mathrm{inf}} \cdot E_c(D) \mathrm{d}D = {\mathrm{BR}}_{\mathrm{k}} \cdot \mathrm{vl_{in}} \cdot f_{\mathrm{inf}} \cdot E_{c}^{\mathrm{total}}$

for 

$E_{c}^{\mathrm{total}} = \int_{D_{\mathrm{min}}}^{D_{\mathrm{max}}} E_c(D) \mathrm{d}D $

using Monte Carlo integration.

### Distribution of the Particle Diameter
When Monte Carlo integrating over the particle diameter, a probability distribution $\mathrm{p}_D(D)$ is needed for sampling of the particle diameter $D$. 
Observe that

$\mathrm{p}_D(D)=\frac{N_p(D)}{K}=\sum_{i \in I(j)} \frac{c_{n,i}}{K}\left[\frac{1}{D\sqrt{2 \pi} \sigma_{D_i}} \exp{-\frac{(\ln D -\mu_{D_i})^2}{2 (\sigma_{D_i})^2}}\right]$

is a mixture distribution: the sum of three log-normal probability distributions weighed by $w_i = \frac{c_{n,i}}{K}$ such that $w_i>0$ and $\sum_{i \in I(j)} w_i =1$. 

In the CAiMIRA model, $D$ is sampled from $\mathrm{p}_D(D)$ truncated between $D_{\mathrm{min}}$ and $D_{\mathrm{min}}$ when calling the function `calculator.models.monte_carlo.data.expiration_distribution()`, which retrieves the truncated $\mathrm{p}_D(D)$ from `calculator.models.monte_carlo.data.BLOModel`.

<details>
<summary>Monte Carlo Integration</summary>
Monte Carlo integration takes advantage of the fact that the expected value of a function g of a random variable D can be approximated by drawing samples {$D_1$, $D_2$, ...,$ D_S$} from the probability distribution $\mathrm{p}_D(D)$ and compute the average. That is,

$E[g(D)] = \int_{\mathrm{D_{min}}}^{\mathrm{D_{max}}} \mathrm{g}(D) \cdot \mathrm{p}_D(D) \mathrm{d}D \approx \frac{1}{S}\sum_{i=1}^S \mathrm{g}(D_i)$ 

The approximation improves for a larger number of samples. For computational efficiency, however, the number of samples should not be unneccecarily high. The lower the variability of p(D), the less samples are needed to stabilize the results. Therefore, one wish to choose a probability distribution $\mathrm{p}_D(D)$  that contains as much information about D as possible.
</details>

Note that the analytical integrals approximated by Monte Carlo integration in CAiMIRA does not explisitly include $\mathrm{p}_D(D)$. Analytically, one therefore computes $\frac{1}{S}\sum_{i=1}^S \frac{\mathrm{h}(D_i)}{\mathrm{p}_D(D_i)}$.

Since every quantity $\mathrm{h}(D)$ that is approximated by Monte Carlo integration in the CAiMIRA model has $N_p(D)$ as a linear factor, which will cancel the $N_p(D)$ factor of $\mathrm{p}_D(D)$, the fraction $\frac{\mathrm{h}(D)}{\mathrm{p}_D(D)}$ will not include $N_p(D)$. Essentially, this means $N_p(D)$ is "replaced" by $K$ in the equation for $E_{c}(D)$ in the model implementation. For example, one therefore computes 

$E_{c}^{\mathrm{total}} = \int_{D_{\mathrm{min}}}^{D_{\mathrm{max}}} \frac{E_c(D) \cdot K}{N_p(D)} \cdot \mathrm{p}_D(D) \mathrm{d}D \approx \frac{1}{S}\sum_{i=1}^S \frac{E_c(D) \cdot K}{N_p(D)}$.


### Computation of the Emission Rate
The computation of the emission rate $\mathrm{vR}(D)$ in CAiMIRA can be divided into three steps:

1. Calculate the diameter-**independent** component of $\mathrm{vR}(D)$, i.e. ${\mathrm{BR}}_{\mathrm{k}} \cdot \mathrm{vl_{in}} \cdot f_{\mathrm{inf}}$, in `caimira.models.models.InfectedPopulation.emission_rate_per_aerosol_per_person_when_present()`. 
2. Draw S samples {$D_1$, $D_2$, ...,$D_S$} from $\mathrm{p}_D(D)$  (default S = 250 000 samples) when creating an **Expiration** object by calling the function `calculator.models.monte_carlo.data.expiration_distribution()`.
3. Compute the diameter-**dependent** $\frac{E_c(D_i) \cdot K}{N_p(D_i)}$ for every $D_i \in ${$D_1$, $D_2$, ...,$D_S$} in `caimira.models.models.InfectedPopulation.aerosols()`. WRONG, why multiply by $cn$ also?

The emission rate (per person infected) $\mathrm{vR(D)}$ can be computed by: `caimira.models.models._PopulationWithVirus.emission_rate_per_person_when_present()`, outputting a vector $[\mathrm{vR(D_1)}, \mathrm{vR(D_2)}, ..., \mathrm{vR(D_S)}]$ who's average is $\mathrm{vR}^{total}$.

By default, however, the diameter-dependence is kept at this stage because more diameter-dependent variables will be introduced downstream in the model before Monte-Carlo integrating over the aerosol sizes to obtain the dose $\mathrm{vD^{total}}$.

### Storage of Intermediate Computations
The methods for computing the components of the emission rate can be accessed through the class **InfectedPopulation**, representing a population of infected with a certain number of people, all with the same expirational activity, physical activity, virus, face mask, immunity and (incremental) presence. **InfectedPopulation** is initialized an **Expiration** object, an **Activity** object, a **Virus** object, a **Mask** object, a float host_immunity, and an **Interval** object corresponding to those properties. Furthermore, **InfectedPopulation** is initialized with by **DataRegistry** and the integer number of people in the infected population.

The **Expiration** object (`caimira.models.models.Expiration`) represents the expiration of aerosols by an infected person, and is initialized by an S-dimentional array (or a single float if S=1) of the samples {$D_1$, $D_2$, ...,$D_S$} drawn from $\mathrm{p}_D(D)$.The samples {$D_1$, $D_2$, ...,$D_S$} are generated by **CustomKernel** (`caimira.calculator.models.monte_carlo.sampleable.CustomKernel`). The **CustomKernel** is built for the distribution $\mathrm{p}_D(D)$ defined by the `distribution()` method of **BLOModel** (`caimira.models.monte_carlo.data.BLOmodel`). **Expiration** is also passed a float $cn$ upon initialization, acting as a scaling factor computed as the integral over every mode in $\{\mathrm{B},\mathrm{L},\mathrm{O}\}$ between $D_{\mathrm{min}}$ and $D_{\mathrm{max}}$ in `BLOModel.integrate()`. The **BLOModel** is initialized by a set of BLO_factors corresponding to the type of expirational activity performed. Consult `caimira.models.monte_carlo.data.expiration_distribution()` for further details on how **Expiration** is initialized.

In the property `Expiration.particle`, the class **Particle** (representing virus-laden aerosols) is initialized with the array of diameters stored in **Expiration**. **Particle** contains methods for computing the diameter-dependent deposition factor and settling velocity of aerosols, which will be used downstream in the model.


## Removal
The viral **viral removal rate** is given by

$\lambda_{\mathrm{vRR}}(t,D) = \lambda_{\mathrm{ACH}}(t)+\lambda_{\mathrm{dep}}(D)+\lambda_{\mathrm{bio}}$

where $\lambda_{\mathrm{ACH}}(t)$ is the air exchange per hour, $\\lambda_{\mathrm{dep}}(D)$ is the particle deposition, and $\lambda_{\mathrm{bio}}$ is the biological decay. The diameter-dependent viral removal rate at a given time is calculated by `caimira.models.models.ConcentrationModel.removal_rate()`.


## Concentration
### Long-Range Compartment
### Short-Range Compartment
### Separation and Averaging of Monte Carlo Random Variables
## Dose
### Separation, Averaging, and Integration of Monte Carlo Random Variables
## Infection Probability


## Separation of Random Variables

It is important to distinguish between 1) Monte-Carlo random variables (which are vectorized independently on its diameter-dependence) and 2) numerical Monte-Carlo integration for the diameter-dependence.
Since the integral of the diameter-dependent variables are solved when computing the dose – $\mathrm{vD^{total}}$ – while performing some of the intermediate calculations,
we normalize the results by *dividing* by the Monte-Carlo variables that are diameter-independent, so that they are not considered in the Monte-Carlo integration (e.g. the **viral load** parameter, or the result of the `caimira.models.models.InfectedPopulation.emission_rate_per_aerosol_per_person_when_present()` method).


## Virus Concentration - C(t, D)

The estimate of the concentration of virus-laden particles in a given room is based on a two-box exposure model:

* **Box 1** - long-range exposure: also known as the *background* concentration, corresponds to the exposure of airborne virions where the susceptible (exposed) host is more than 2 m away from the infected host(s), considering the result of a mass balance equation between the emission rate of the infected host(s) and the removal rates from the environmental/virological characteristics.
* **Box 2** - short-range exposure: also known as the *exhaled jet* concentration in close-proximity, corresponds to the exposure of airborne virions where the susceptible (exposed) host is distanced between 0.5 and 2 m from an infected host, considering the result of a two-stage exhaled jet model.

Note that most of the methods used to calculate the concentration are defined in the superclass `caimira.models.models._ConcentrationModelBase()`, while the specific methods for the long-range virus concentration are part of the subclass `caimira.models.models.ConcentrationModel()`.
The specific removal rate, minimum background concentration and normalization factors will depend on what concentration is being calculated (e.g. viral concentration or CO<sub>2</sub> concentration) and are respectively defined in `caimira.models.models._ConcentrationModelBase.removal_rate()`, `caimira.models.models._ConcentrationModelBase.min_background_concentration()` and `caimira.models.models._ConcentrationModelBase.normalization_factor()`.

### Long-range approach

The long-range concentration of virus-laden aerosols of a given size $D$, that is based on the mass balance equation between the emission and removal rates, is given by:

$C_{\mathrm{LR}}(t, D)=\frac{\mathrm{vR}(D) \cdot N_{\mathrm{inf}}}{\lambda_{\mathrm{vRR}}(D) \cdot V_r}-\left (\frac{\mathrm{vR}(D) \cdot N_{\mathrm{inf}}}{\lambda_{\mathrm{vRR}}(D) \cdot V_r}-C_0(D) \right )e^{-\lambda_{\mathrm{vRR}}(D)t}$ ,

and computed, as a function of the exposure time and particle diameter, in the `caimira.models.models._ConcentrationModelBase.concentration()` method.
The long-range concentration, integrated over the exposure time (in piecewise constant steps), $C(D)$, is given by `caimira.models.models._ConcentrationModelBase.integrated_concentration()`.

In the $C_{\mathrm{LR}}(t, D)$ equation above, the **emission rate** - $\mathrm{vR}(D)$ - and the **viral removal rate** - $\lambda_{\mathrm{vRR}}(D)$, `caimira.models.models.ConcentrationModel.infectious_virus_removal_rate()` - are both diameter-dependent.
One can show that the resulting concentration is always proportional to the emission rate $\mathrm{vR}(D)$. Hence, for computational speed-up purposes
the code computes first a normalized version of the concentration, i.e. divided by the emission rate, before multiplying by $\mathrm{vR}(D)$.

To summarize, we can split the concentration in two different formulations:

* Normalized concentration `caimira.models.models._ConcentrationModelBase._normed_concentration()`: $\mathrm{C_\mathrm{LR, normed}}(t, D)$ that computes the concentration without including the emission rate per person infected.
* Concentration `caimira.models.models._ConcentrationModelBase.concentration()` : $C_{\mathrm{LR}}(t, D) = \mathrm{C_\mathrm{LR, normed}}(t, D) \cdot \mathrm{vR}(D)$, where $\mathrm{vR}(D)$ is the result of the `caimira.models.models._PopulationWithVirus.emission_rate_per_person_when_present()` method.

Note that in order to get the total concentration value in this stage, the final result should be averaged over the particle diameters (i.e. Monte-Carlo integration over diameters, see above).
For the calculator app report, the total concentration (MC integral over the diameter) is performed only when generating the plot.
Otherwise, the diameter-dependence continues until we compute the inhaled dose in the `caimira.models.models.ExposureModel` class.

The following methods calculate the integrated concentration between two times. They are mostly used when calculating the **dose**:

* `caimira.models.models._ConcentrationModelBase.normed_integrated_concentration()`, $\mathrm{C_\mathrm{normed}}(D)$ that returns the integrated long-range concentration of viruses in the air, between any two times, normalized by the emission rate per person infected. Note that this method performs the integral between any two times of the previously mentioned `caimira.models.models._ConcentrationModelBase._normed_concentration()` method.
* `caimira.models.models._ConcentrationModelBase.integrated_concentration()`, $C(D)$, that returns the same result as the previous one, but multiplied by the emission rate (per person infected).

The integral over the exposure times is calculated directly in the class (integrated methods).

### Short-range approach

The short-range concentration is the result of a two-stage exhaled jet model developed by Jia, W. et al. <sup>[1](#id7)</sup> and is expressed as:

$C_{\mathrm{SR}}(t, D) = C_{\mathrm{LR}} (t, D) + \frac{1}{S({x})} \cdot (C_{0, \mathrm{SR}}(D) - C_{\mathrm{LR}, 100μm}(t, D))$ ,

where $S(x)$ is the dilution factor due to jet dynamics, as a function of the interpersonal distance $x$ and $C_{0, \mathrm{SR}}(D)$ corresponds to the initial concentration of virions at the mouth/nose outlet during exhalation.
$C_{\mathrm{LR}, 100μm}(t, D)$ is the long-range concentration, calculated in `caimira.models.models._ConcentrationModelBase.concentration()` method but **interpolated** to the diameter range used for close-proximity (from 0 to 100μm).
Note that $C_{0, \mathrm{SR}}(D)$ is constant over time, hence only dependent on the particle diameter distribution.

For code simplification, we split the $C_{\mathrm{SR}}(t, D)$ equation into two components:

* short-range component: $\frac{1}{S({x})} \cdot (C_{0, \mathrm{SR}}(D) - C_{\mathrm{LR}, 100μm}(t, D))$, dealt with in the dataclass `caimira.models.models.ShortRangeModel`.
* long-range component: $C_{\mathrm{LR}} (t, D)$.

The short-range data class (`caimira.models.models.ShortRangeModel`) models the short-range component of a close-range interaction **concentration** and the respective **dilution_factor**.
Its inputs are the **expiration** definition, the **activity type**, the **presence time**, and the **interpersonal distance** between any two individuals.
When generating a full model, the short-range class is defined with a new **Expiration** distribution,
given that the **min** and **max** diameters for the short-range interactions are different from those used in the long-range concentration (the idea is that very large particles should not be considered in the long-range case as they fall rapidly on the floor,
while they must be in for the short-range case).

As mentioned in Jia, W. et al. <sup>[1](#id7)</sup>, the jet concentration depends on the **long-range concentration** of viruses.
Here, once again, we shall normalize the short-range concentration to the diameter-independent quantities.
IMPORTANT NOTE: since the susceptible host is physically closer to the infector, the emitted particles are larger in size,
hence a new distribution of diameters should be taken into consideration.
As opposed to $D_{\mathrm{max}} = 20\mathrm{μm}$ for the long-range MC integration, the short-range model will assume a $D_{\mathrm{max}} = 100\mathrm{μm}$.
Very similar to what we did with the **emission rate**, we need to calculate the scaling factor from the probability distribution, $N_p(D)$ - $cn$, as well as the **volume concentration** for those diameters.

During a given exposure time, multiple short-range interactions can be defined in the model.
In addition, for each individual interaction, the expiration type may be different.

To calculate the short-range component, we first need to calculate what is the **dilution factor**, that depends on the distance $x$ as a random variable, from a log normal distribution in `caimira.models.monte_carlo.data.short_range_distances()`.
This factor is calculated in a two-stage expiratory jet model, with its transition point defined as follows:

$\mathrm{xstar}=𝛽_{\mathrm{x1}} (Q_{\mathrm{exh}} \cdot u_{0})^\frac{1}{4} \cdot (\mathrm{tstar} + t_{0})^\frac{1}{2} - x_{0}$,

where $Q_{\mathrm{exh}}= φ \mathrm{BR}$ is the expired flow rate during the expiration period, in $m^{3} s^{-1}$, φ is the exhalation coefficient
(dimensionless) and represents the ratio between the total period of a breathing cycle and the duration of the exhalation alone.
Assuming the duration of the inhalation part is equal to the exhalation and one starts immediately after the other, φ will always be equal to 2 no matter what is the breating cycle time. $\mathrm{BR}$ is the given exhalation rate.
$u_{0}$ is the expired jet speed (in $m s^{-1}$) given by $u_{0}=\frac{Q_{\mathrm{exh}}}{A_{m}}$, $A_{m}$ being the area of the mouth assuming a perfect circle (average mouth_diameter of 0.02m).
The time of the transition point $\mathrm{tstar}$ is defined as 2s and corresponds to the end of the exhalation period, i.e. when the jet is interrupted. The distance of the virtual origin of the puff-like stage is defined by
$x_{0}=\frac{\textrm{mouth_diameter}}{2𝛽_{\mathrm{r1}}}$ (in m), and the corresponding time is given by $t_{0} = \frac{\sqrt{\pi} \cdot \textrm{mouth_diameter}^3}{8𝛽_{\mathrm{r1}}^2𝛽_{\mathrm{x1}}^2Q_{exh}}$ (in s).
Having the distance for the transition point, we can calculate the dilution factor at the transition point, defined as follows:

$\mathrm{Sxstar}=2𝛽_{\mathrm{r1}}\frac{(xstar + x_{0})}{\textrm{mouth_diameter}}$.

The remaining dilution factors, either in the jet- or puff-like stages are calculated as follows:

$\mathrm{factors}(x)=\begin{cases}\hfil 2𝛽_{\mathrm{r1}}\frac{(x + x_{0})}{\textrm{mouth_diameter}} & \textrm{if } x < \mathrm{xstar},\\\hfil \mathrm{Sxstar} \cdot \biggl(1 + \frac{𝛽_{\mathrm{r2}}(x - xstar)}{𝛽_{\mathrm{r1}}(xstar + x_{0})}\biggl)^3 & \textrm{if } x > \mathrm{xstar}.\end{cases}$

The penetration coefficients in the jet-like stage $𝛽_{\mathrm{r1}}$, $𝛽_{\mathrm{r2}}$ and $𝛽_{\mathrm{x1}}$ are defined by the following empirical values 0.18, 0.2, and 2.4 respectively. The dilution factor for each distance $x$ is then stored in the $\mathrm{factors}$ array that is returned by the method.

Having the dilution factors, the **initial concentration of virions at the mouth/nose**, $C_{0, \mathrm{SR}}(D)$, is calculated as follows:

$C_{0, \mathrm{SR}}(D) = N_p(D) \cdot V_p(D) \cdot \mathrm{vl_{in}} \cdot 10^{-6}$,
given by `caimira.models.models.Expiration.jet_origin_concentration()`. It computes the same quantity as `caimira.models.models.Expiration.aerosols()`, except for the mask inclusion. As previously mentioned, it is normalized by the **viral load**, which is a diameter-independent property.
Note, the $10^{-6}$ factor corresponds to the conversion from $\mathrm{μm}^{3} \cdot \mathrm{cm}^{-3}$ to $\mathrm{mL} \cdot m^{-3}$.

Note that similarly to the long-range approach, the MC integral over the diameters is not calculated at this stage.

For consistency, the long-range concentration parameter, $C_{\mathrm{LR}, 100\mathrm{μm}}(t, D)$ in the `caimira.models.models.ShortRangeModel` class **only**,
shall also be normalized by the **viral load** and **fraction of infectious virus**, since in the short-range model the diameter range is different than at long-range (as mentioned above),
we need to account for that difference.
The former operation is given in method `caimira.models.models.ShortRangeModel._long_range_normed_concentration()`. For the diameter range difference, there are a few options:
one solution would be to recompute the values a second time using $D_{\mathrm{max}} = 100\mathrm{μm}$;
or perform a approximation using linear interpolation, which is possible and more effective in terms of performance. We decided to adopt the interpolation solution.
The set of points with a known value are given by the default expiration particle diameters for long-range, i.e. from 0 to 20 $\mathrm{μm}$.
The set of points we want the interpolated values are given by the short-range expiration particle diameters, i.e. from 0 to 100 $\mathrm{μm}$.

To summarize, in the code, $C_{\mathrm{SR}}(t, D)$ is computed as follows:

* calculate the dilution_factor - $S({x})$ - in the method `caimira.models.models.ShortRangeModel.dilution_factor()`, with the distance $x$ as a random variable (log normal distribution in `caimira.models.monte_carlo.data.short_range_distances()`)
* compute $\frac{1}{S({x})} \cdot (C_{0, \mathrm{SR}}(D) - C_{\mathrm{LR}, 100\mathrm{μm}}(t, D))$ in method `caimira.models.models.ShortRangeModel.normed_concentration()`,
* multiply by the diameter-independent parameters, viral load and $\mathrm{f_{inf}}$, in method `caimira.models.models.ShortRangeModel.short_range_concentration()`
* complete the equation of $C_{\mathrm{SR}}(t, D)$ by adding the long-range concentration from the `caimira.models.models._ConcentrationModelBase.concentration()` (all integrated over $D$), returning the final short-range concentration value for a given time and expiration activity. This is done at the level of the Exposure Model (`caimira.models.models.ExposureModel.concentration()`).

Note that `caimira.models.models.ShortRangeModel._normed_concentration()` method is different from `caimira.models.models._ConcentrationModelBase._normed_concentration()` and `caimira.models.models._ConcentrationModelBase.concentration()` differs from `caimira.models.models.ExposureModel.concentration()`.

Unless one is computing the mean concentration values (e.g. for the plots in the report), the diameter-dependence is kept at this stage. Since other parameters downstream in the code are also diameter-dependent, the Monte-Carlo integration over the particle sizes is computed at the level of the dose $\mathrm{vD^{total}}$.
In case one would like to have intermediate results for the initial short-range concentration, this is done at the `caimira.models.models.ExposureModel` class level.

## Dose - vD

The term dose refers to the number of viable virions (infectious virus) that will contribute to a potential infection.
It results in a combination of several properties: exposure, inhalation rate, aerosol deposition in the respiratory tract and the effect of protective equipment such as masks.

The receiving dose, which is inhaled by the exposed host, in infectious virions per unit diameter (diameter-dependence),
is calculated by first integrating the viral concentration profile (for a given particle diameter) over the exposure time and multiplying by scaling factors such as the proportion of virions which are infectious and the deposition fraction,
as well as the inhalation rate and the effect of masks:

$\mathrm{vD}(D) = \int_{t1}^{t2}C(t, D)\;\mathrm{d}t \cdot \mathrm{BR}_{\mathrm{k}} \cdot f_{\mathrm{dep}}(D) \cdot (1-\eta_{\mathrm{in}})$ .

where $C(t, D)$ is the concentration value at a given time, which can be either the short- or long-range concentration, $f_{\mathrm{dep}}(D)$ is the (diameter-dependent) deposition fraction in the respiratory tract, $\mathrm{BR}_{\mathrm{k}}$ is the inhalation rate and $\eta_{\mathrm{in}}$ is the inward efficiency of the face mask.

Given that the calculation is diameter-dependent, to calculate the dose in the model, the code contains different methods that consider the parameters that are dependent on the aerosol size, $D$.
The total dose, at the end of the exposure scenario, results from the sum of the dose accumulated over time, integrated over particle diameters:

$\mathrm{vD^{total}} = \int_0^{D_{\mathrm{max}}} \mathrm{vD}(D) \, \mathrm{d}D$ .

This calculation is computed using a Monte-Carlo integration over $D$. As previously described, many different parameters samples are generated using the probability distribution from the $N_p(D)$ equation.
The dose for each of them is then computed, and their **average** value over all samples represents a good approximation of the total dose, provided that the number of samples is large enough.

### Long-range approach

Regarding the concentration part of the long-range exposure (concentration integrated over time, $\int_{t1}^{t2}C_{\mathrm{LR}}(t, D)\;\mathrm{d}t$), the respective method is `caimira.models.models.ExposureModel._long_range_normed_exposure_between_bounds()`,
which uses the long-range exposure (concentration) between two bounds (time1 and time2), normalized by the emission rate of the infected population (per person infected), calculated from `caimira.models.models._ConcentrationModelBase.normed_integrated_concentration()`.
The former method filters out the given bounds considering the breaks through the day (i.e. the time intervals during which there is no exposition to the virus) and retrieves the integrated long-range concentration of viruses in the air between any two times.

After the calculations of the integrated concentration over the time, in order to calculate the final dose, we have to compute the remaining factors in the above equation.
Note that the **Monte-Carlo integration over the diameters is performed at this stage**, where all the diameter-dependent parameters are grouped together to calculate the final average (`np.mean()`).

Since, in the previous chapters, the quantities where normalised by the emission rate per person infected, one will need to re-incorporate it in the equations before performing the MC integrations over $D$.
For that we need to split $\mathrm{vR}(D)$ (`caimira.models.models._PopulationWithVirus.emission_rate_per_person_when_present()`) in diameter-dependent and diameter-independent quantities:

$\mathrm{vR}(D) = \mathrm{vR}(D-\mathrm{dependent}) \times \mathrm{vR}(D-\mathrm{independent})$

with

$\mathrm{vR}(D-\mathrm{dependent}) = \mathrm{cn} \cdot V_p(D) \cdot (1 − \mathrm{η_{out}}(D))$ - `caimira.models.models.InfectedPopulation.aerosols()`

$\mathrm{vR}(D-\mathrm{independent}) = \mathrm{vl_{in}} \cdot \mathrm{f_{inf}} \cdot \mathrm{BR_{k}}$ - `caimira.models.models.InfectedPopulation.emission_rate_per_aerosol_per_person_when_present()`

In other words, in the code the procedure is the following (all performed in `caimira.models.models.ExposureModel.long_range_deposited_exposure_between_bounds()` method):

* start re-incorporating the emission rate by first multiplying by the diameter-dependent quantities: $\mathrm{vD_{aerosol}}(D) = (\int_{t1}^{t2}C_{\mathrm{LR}}(t, D)\;\mathrm{d}t \cdot \mathrm{vR}(D-\mathrm{dependent}) \cdot f_{\mathrm{dep}}(D))$, in `caimira.models.models.ExposureModel.long_range_deposited_exposure_between_bounds()` method;
* perform the **MC integration over the diameters**, which is considered equivalent as the mean of the distribution if the sample size is large enough: $\mathrm{vD_{aerosol}} = \mathrm{np.mean}(\mathrm{vD_{aerosol}}(D))$;
* multiply the result with the remaining diameter-independent quantities of the emission rate used previously to normalize: $\mathrm{vD_{emission-rate}} = \mathrm{vD_{aerosol}} \cdot \mathrm{vR}(D-\mathrm{independent})$;
* in order to complete the equation, multiply by the remaining diameter-independent variables in $\mathrm{vD}$ to obtain the total value: $\mathrm{vD^{total}} = \mathrm{vD_{emission-rate}} \cdot \mathrm{BR}_{\mathrm{k}} \cdot (1-\eta_{\mathrm{in}})$;
* in the end, the dose is a vectorized float used in the probability of infection formula.

**Note**: The aerosol volume concentration (*aerosols*) is introduced because the integrated concentration over the time was previously normalized by the emission rate (per person).
Here, to calculate the integral over the diameters we also need to consider the diameter-dependent variables that are on the emission rate, represented by the aerosol volume concentration which depends on the diameter and on the mask type:

$\mathrm{aerosols} = \mathrm{cn} \cdot V_p(D) \cdot (1 − \mathrm{η_{out}}(D))$ .
The $\mathrm{cn}$ factor, which represents the total number of aerosols emitted, is introduced here as a scaling factor, as otherwise the Monte-Carlo integral would be normalized to 1 as the probability distribution.

**Note**: for simplification of the notations, here the dose corresponding exclusively to the long-range contribution is written as $\mathrm{vD_{LR}}(D)= \mathrm{vD}(D)$.

In the end, the governing method is `caimira.models.models.ExposureModel.deposited_exposure_between_bounds()`, in which the deposited_exposure is equal to long_range_deposited_exposure_between_bounds in the absence of short-range interactions.

### Short-range approach

In theory, the dose during a close-proximity interaction (short-range) is simply added to the dose inhaled due to the long-range and may be defined as follows:

$\mathrm{vD}(D)= \mathrm{vD^{LR}}(D) + \sum\limits_{i=1}^{n} \int_{t1}^{t2}C_{\mathrm{SR}}(t, D)\;\mathrm{d}t \cdot \mathrm{BR}_{\mathrm{k}} \cdot f_{\mathrm{dep}}(D) \cdot (1-\eta_{\mathrm{in}})$ ,

where $\mathrm{vD_{LR}}(D)$ is the long-range, diameter-dependent dose computed previously.

From above, the short-range concentration:

$C_{\mathrm{SR}}(t, D) = C_{\mathrm{LR}, 100μm} (t, D) + \frac{1}{S({x})} \cdot (C_{0, \mathrm{SR}}(D) - C_{\mathrm{LR}, 100μm}(t, D))$ ,

In the code, the method that returns the value for the total dose (independently if it is short- or long-range) is given by `caimira.models.models.ExposureModel.deposited_exposure_between_bounds()`.
For code simplification, we split the $C_{\mathrm{SR}}(t, D)$ equation into two components:

* short-range component: $\frac{1}{S({x})} \cdot (C_{0, \mathrm{SR}}(D) - C_{\mathrm{LR}, 100μm}(t, D))$;
* long-range component: $C_{\mathrm{LR}} (t, D)$.

Similarly as above, first we perform the multiplications by the diameter-dependent variables so that we can profit from the Monte-Carlo integration. Then we multiply the final value by the diameter-independent variables.
The method `caimira.models.models.ShortRangeModel._normed_jet_exposure_between_bounds()` gets the integrated short-range concentration of viruses in the air between the times start and stop, normalized by the **viral load** and **fraction of infectious virus**,
and excluding the **jet dilution** since it is also diameter-independent.
This corresponds to $C_{0, \mathrm{SR}}(D)$.

The method `caimira.models.models.ShortRangeModel._normed_interpolated_longrange_exposure_between_bounds()` retrieves the integrated short-range concentration due to the background concentration,
normalized by the **viral load**, **fraction of infectious virus** and the **breathing rate**, and excluding the jet **dilution**.
The result is then interpolated to the particle diameter range used in the short-range model (i.e. 100 μm).
This corresponds to $\int_{t1}^{t2} C_{\mathrm{LR}, 100\mathrm{μm}} (t, D)\mathrm{d}t$.
Very similar to the long-range procedure, this method performs the integral of the concentration for the given time boundaries.

Once we have the integral of the concentration normalized by the diameter-independent quantities, we multiply this result by the remaining diameter-dependent properties to perform the integral
over the particle diameters, including the **fraction deposited** computed with an evaporation factor of 1 (as the aerosols do not have time to evaporate during a short-range interaction).
This operation is performed with the MC intergration using the *mean*, which corresponds to:
$\int_{0}^{D_{max}}C_{\mathrm{SR}}(t, D) \cdot f_{\mathrm{dep}}(D) \;\mathrm{d}D$ .

Note that in the code we perform the subtraction between the concentration at the jet origin and the long-range concentration of viruses in two steps when we calculate the dose,
since the contribution of the diameter-dependent variable $f_{\mathrm{dep}}$ has to be multiplied separately in substractions:

integral_over_diameters = $((C_{0, \mathrm{SR}} \cdot f_{\mathrm{dep}}) - (C_{\mathrm{LR}, 100μm} (t, D) \cdot f_{\mathrm{dep}})) \cdot \mathrm{mean()}$ .

Then, we add the contribution to the result of the diameter-**independent** vectorized properties **in two seperate phases**:

* multiply by the diameter-independent properties that are dependent on the **activity type** of the different short-range interactions: **breathing rate** and **dilution factor** - within the *for* cycle;
* multiply by the other properties that are **not** dependent on the type of short-range interactions: **viral load**, **fraction of infectious virus** and **inwards mask efficiency**.

The final operation in the `caimira.models.models.ExposureModel.deposited_exposure_between_bounds()` accounts for the addition of the long-range component of the dose.

If short-range interactions exist: the long-range component is added to the already calculated short-range component (deposited_exposure), hence completing $C_{\mathrm{SR}}$.
If the are no short-range interactions: the short-range component (deposited_exposure) is zero, hence the result is equal solely to the long-range component $C_{\mathrm{LR}}$.

## CO<sub>2</sub> Concentration

The estimate of the concentration of CO<sub>2</sub> in a given room to indicate the air quality is given by the same approach as for the long-range virus concentration,
$C_{\mathrm{LR}}(t, D)$, where $C_0(D)$ is considered to be the background (outdoor) CO<sub>2</sub> concentration (`caimira.models.models.CO2ConcentrationModel.CO2_atmosphere_concentration()`).

In order to compute the CO<sub>2</sub> concentration one should then simply use the `caimira.models.models.CO2ConcentrationModel.concentration()` method.
A fraction of 4.2% of the exhalation rate of the defined activity was considered as supplied to the room (`caimira.models.models.CO2ConcentrationModel.CO2_fraction_exhaled()`).

Note still that nothing depends on the aerosol diameter $D$ in this case (no particles are involved) - hence in this class all parameters are constant w.r.t $D$.

Since the CO<sub>2</sub> concentration differs from the virus concentration, the specific removal rate, CO<sub>2</sub> atmospheric concentration and normalization factors are respectively defined in `caimira.models.models.CO2ConcentrationModel.removal_rate()`,
`caimira.models.models.CO2ConcentrationModel.min_background_concentration()` and `caimira.models.models.CO2ConcentrationModel.normalization_factor()`.

## References

* <a id='id7'>**[1]**</a> Jia, Wei, et al. “Exposure and respiratory infection risk via the short-range airborne route.” Building and environment 219 (2022): 109166. [doi.org/10.1016/j.buildenv.2022.109166](https://doi.org/10.1016/j.buildenv.2022.109166)
* <a id='id8'>**[2]**</a> Henriques, Andre, et al. “Modelling airborne transmission of SARS-CoV-2 using CARA: risk assessment for enclosed spaces.” Interface Focus 12.2 (2022): 20210076. [doi.org/10.1098/rsfs.2021.0076](https://doi.org/10.1098/rsfs.2021.0076)
