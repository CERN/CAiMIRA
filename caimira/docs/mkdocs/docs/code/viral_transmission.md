# Physics of Viral Transmission

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
The `caimira.calculator.models.models.py` (hereafter abbreviated as `models`) and `caimira.calculator.models.monte_carlo` (hereafter abbreviated as `monte_carlo`) implements the core CAiMIRA methods. A useful feature of the implementation is that we can benefit from vectorization, which allows running multiple parameterizations of the model at the same time.


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

for
$K=\int_{D_{\mathrm{min}}}^{D_{\mathrm{max}}} N_p(D) \mathrm{d}D $
is a mixture distribution: the sum of three truncated and scaled log-normal probability distributions. 

In the CAiMIRA model, $D$ is sampled from $\mathrm{p}_D(D)$ truncated between $D_{\mathrm{min}}$ and $D_{\mathrm{min}}$ when calling the function `monte_carlo.data.expiration_distribution()`, which retrieves the truncated $\mathrm{p}_D(D)$ from `monte_carlo.data.BLOModel`.

<details>
<summary>Monte Carlo Integration</summary>
Monte Carlo integration takes advantage of the fact that the expected value of a function g of a random variable D can be approximated by drawing samples {$D_1$, $D_2$, ...,$ D_S$} from the probability distribution $\mathrm{p}_D(D)$ and compute the average. That is,

$E[g(D)] = \int_{\mathrm{D_{min}}}^{\mathrm{D_{max}}} \mathrm{g}(D) \cdot \mathrm{p}_D(D) \mathrm{d}D \approx \frac{1}{S}\sum_{i=1}^S \mathrm{g}(D_i)$ 

The approximation improves for a larger number of samples. For computational efficiency, however, the number of samples should not be unneccecarily high. The lower the variability of p(D), the less samples are needed to stabilize the results. Therefore, one wish to choose a probability distribution $\mathrm{p}_D(D)$  that contains as much information about D as possible.
</details>

Note that the analytical integrals approximated by Monte Carlo integration in CAiMIRA does not explisitly include $\mathrm{p}_D(D)$. Analytically, one therefore computes $\frac{1}{S}\sum_{i=1}^S \frac{\mathrm{h}(D_i)}{\mathrm{p}_D(D_i)}$.
Every quantity $\mathrm{h}(D)$ that is approximated by Monte Carlo integration in the CAiMIRA model has $N_p(D)$ as a linear factor, which will cancel the $N_p(D)$ factor of $\mathrm{p}_D(D)$, the fraction $\frac{\mathrm{h}(D)}{\mathrm{p}_D(D)}$ will not include $N_p(D)$. Essentially, this means $N_p(D)$ is "replaced" by $K$ in the equation for $E_{c}(D)$ in the model implementation. For example, one therefore computes 

$E_{c}^{\mathrm{total}} = \int_{D_{\mathrm{min}}}^{D_{\mathrm{max}}} \frac{E_c(D) \cdot K}{N_p(D)} \cdot \mathrm{p}_D(D) \mathrm{d}D \approx \frac{1}{S}\sum_{i=1}^S \frac{E_c(D) \cdot K}{N_p(D)}$.

### Computation of the Emission Rate
The computation of the emission rate $\mathrm{vR}(D)$ in CAiMIRA can be divided into three steps:

* Calculate the diameter-**independent** component of $\mathrm{vR}(D)$, i.e. ${\mathrm{BR}}_{\mathrm{k}} \cdot \mathrm{vl_{in}} \cdot f_{\mathrm{inf}}$, in `models.InfectedPopulation.emission_rate_per_aerosol_per_person_when_present()`. 
* Draw S samples {$D_1$, $D_2$, ...,$D_S$} from $\mathrm{p}_D(D)$  (default S = 250 000 samples) when creating an **Expiration** object by calling the function `monte_carlo.data.expiration_distribution()`.
* Compute the diameter-**dependent** $\frac{E_c(D_i) \cdot K}{N_p(D_i)}$ for every $D_i \in ${$D_1$, $D_2$, ...,$D_S$} in `models.InfectedPopulation.aerosols()`. WRONG, why multiply by $cn$ also?

The emission rate (per person infected) $\mathrm{vR(D)}$ can be computed by: `models._PopulationWithVirus.emission_rate_per_person_when_present()`, outputting a vector $[\mathrm{vR(D_1)}, \mathrm{vR(D_2)}, ..., \mathrm{vR(D_S)}]$ who's average is $\mathrm{vR}^{total}$.

By default, however, the diameter-dependence is kept at this stage because more diameter-dependent variables will be introduced downstream in the model before Monte-Carlo integrating over the aerosol sizes to obtain the dose $\mathrm{vD^{total}}$.

The methods for computing the components of the emission rate can be accessed through the class **InfectedPopulation**, representing a population of infected with a certain number of people, all with the same expirational activity, physical activity, virus, face mask, immunity and (incremental) presence. **InfectedPopulation** is initialized an **Expiration** object, an **Activity** object, a **Virus** object, a **Mask** object, a float host_immunity, and an **Interval** object corresponding to those properties. Furthermore, **InfectedPopulation** is initialized with by **DataRegistry** and the integer number of people in the infected population.

The **Expiration** object (`models.Expiration`) represents the expiration of aerosols by an infected person, and is initialized by an S-dimentional array (or a single float if S=1) of the samples {$D_1$, $D_2$, ...,$D_S$} drawn from $\mathrm{p}_D(D)$.The samples {$D_1$, $D_2$, ...,$D_S$} are generated by **CustomKernel** (`monte_carlo.sampleable.CustomKernel`). The **CustomKernel** is built for the distribution $\mathrm{p}_D(D)$ defined by the `distribution()` method of **BLOModel** (`monte_carlo.data.BLOmodel`). **Expiration** is also passed a float $cn$ upon initialization, acting as a scaling factor computed as the integral over every mode in $\{\mathrm{B},\mathrm{L},\mathrm{O}\}$ between $D_{\mathrm{min}}$ and $D_{\mathrm{max}}$ in `BLOModel.integrate()`. The **BLOModel** is initialized by a set of BLO_factors corresponding to the type of expirational activity performed. Consult `monte_carlo.data.expiration_distribution()` for further details on how **Expiration** is initialized.

In the property `Expiration.particle`, the class **Particle** (representing virus-laden aerosols) is initialized with the array of diameters stored in **Expiration**. **Particle** contains methods for computing the diameter-dependent deposition factor and settling velocity of aerosols, which will be used downstream in the model.


## Removal
The viral **viral removal rate** is given by

$\lambda_{\mathrm{vRR}}(t,D) = \lambda_{\mathrm{ACH}}(t)+\lambda_{\mathrm{dep}}(D)+\lambda_{\mathrm{bio}}$

where $\lambda_{\mathrm{ACH}}(t)$ is the air exchange per hour, $\\lambda_{\mathrm{dep}}(D)$ is the particle deposition, and $\lambda_{\mathrm{bio}}$ is the biological decay. The diameter-dependent viral removal rate at a given time is calculated by `models.ConcentrationModel.removal_rate()`.


## Viral Concentration
The estimate of the concentration of virus-laden particles in a given room is based on a two-box exposure model:

* **Box 1** - long-range exposure: also known as the *background* concentration, corresponds to the exposure of airborne virions where the susceptible (exposed) host is more than 2 m away from the infected host(s), considering the result of a mass balance equation between the emission rate of the infected host(s) and the removal rates from the environmental/virological characteristics.
* **Box 2** - short-range exposure: also known as the *exhaled jet* concentration in close-proximity, corresponds to the exposure of airborne virions where the susceptible (exposed) host is distanced between 0.5 and 2 m from an infected host, considering the result of a two-stage exhaled jet model.

Most of the methods used to calculate the long-range concentration are defined in the superclass `models._ConcentrationModelBase()`, with the abstract methods `removal_rate()`, `min_background_concentration()`, and `normalization_factor()` implemented for **viral** concentrations specifically in the subclass `models.ConcentrationModel()`. Later, we will see that `models.CO2ConcentrationModel()` also inherits from `models._ConcentrationModelBase()`. The short-range virus concentration is modelled by the independent class `models.ShortRangeModel()`.

### Long-Range Compartment
#### Derivation of the Analytical Long-Range Concentration
Assuming mass balance, the change in the viral concentration equal the difference between the total emission rate per volume and the total removal rate. If we assume all the infected have the same emission rate, the total emission rate per unit volume is the product of $\mathrm{vR(D)}$ and the number of infected $N_{\mathrm{inf}}$ divided by the room volume $V_r$. The total removal rate is the product of the viral removal rate $\lambda_{\mathrm{vRR}}(t,D)$ and the current viral concentration $C_{\mathrm{LR}}(t, D)$. In conclusion, the viral concentration is described by the ordinary differential equation (ODE)

$\frac{\partial C_{\mathrm{LR}}(t, D)}{\partial t} = \frac{\mathrm{vR}(D)\,N_{\mathrm{inf}}}{V_r} - \lambda_{vRR}(D) \cdot C_{\mathrm{LR}}(t, D)$.

Assuming the viral concentration is the only time-dependent variable, this ODE can be solved analytically for a given particle size $D$. The solution might only hold over time intervals $[t_i, t_{i+1}]$ where the assumption that $\lambda_{vRR}(D)$ and $N_{\mathrm{inf}}$ are time-independent holds. In that case, the viral concentration at the end of the previous interval $C_{\mathrm{LR}}(t_i,D)$ can be carried forward as an intital condition to the next interval. 

The homogeneous solution (satisfying 
$\frac{\partial C_{\mathrm{LR}}(t, D)}{\partial t} + \lambda_{vRR}(D)\cdot\,C_{\mathrm{LR}}(t, D) = 0$)
is 
$C_{\mathrm{LR}}(t, D)_{h}=A_1\cdot \exp{-\lambda_{vRR}(D)\cdot t}$. 
Assuming the particular solution is a constant $A_2$ we have the **general solution**

$C_{\mathrm{LR}}(t, D) = A_2 + A_1\cdot \exp{-\lambda_{vRR}(D)\cdot t}$

with derivative

$\frac{\partial C_{\mathrm{LR}}(t, D)}{\partial t} = -A_1\cdot \lambda_{vRR}(D) \cdot \exp{-\lambda_{vRR}(D)\cdot t}$

Combining the two equations containing $\frac{\partial C_{\mathrm{LR}}(t, D)}{\partial t}$ we get

$C_{\mathrm{LR}}(t, D) = \frac{\mathrm{vR(D)}\,N_{\mathrm{inf}}}{\lambda_{vRR}(D)\,V_r} + A_1\cdot \exp{-\lambda_{vRR}(D)\cdot t}$, 

which combined with the general solution yields

$A_2 = \frac{\mathrm{vR(D)}\,N_{\mathrm{inf}}}{\lambda_{vRR}(D)\,V_r}$.

For at the end of the last time interval (at $t=t_i$) the general solution gives
$C_{\mathrm{LR}}(t_i, D) = A_2 + A_1\cdot \exp{-\lambda_{vRR}(D)\cdot t_i}$. 
Hence, 

$A_1 = -\left(\frac{\mathrm{vR(D)}\,N_{\mathrm{inf}}}{\lambda_{vRR}(D)\,V_r}-C_{\mathrm{LR}}(t_i, D)\right) \cdot \exp{\lambda_{vRR}(D)\cdot t_i}$.

In conclusion, the analytical solution of the ODE describing the viral concentration, assuming only the concentration is time-dependent, is

$C_{\mathrm{LR}}(t, D) = \frac{\mathrm{vR(D)}\,N_{\mathrm{inf}}}{\lambda_{vRR}(D)\,V_r} - \left(\left(\frac{\mathrm{vR(D)}\,N_{\mathrm{inf}}}{\lambda_{vRR}(D)\,V_r}- C_{\mathrm{LR}}(t_i, D)\right) \cdot \exp{\lambda_{vRR}(D)\cdot t_i}\right) \exp{-\lambda_{vRR}(D)\cdot t}$

$= \frac{\mathrm{vR(D)}\,N_{\mathrm{inf}}}{\lambda_{vRR}(D)\,V_r} - \left(\frac{\mathrm{vR(D)}\,N_{\mathrm{inf}}}{\lambda_{vRR}(D)\,V_r}-C_{\mathrm{LR}}(t_i, D)\right) \exp{-\lambda_{vRR}(D)\cdot (t-t_i)}$. 


In CAiMIRA, we compute the normaized concentration $\frac{C_{\mathrm{LR}}(t, D)}{\mathrm{vR(D)}}$ in `models._ConcentrationModelBase._normed_concentration()`. 
The normalized concentration $\frac{C_{\mathrm{LR}}(t_i, D)}{\mathrm{vR(D)}}$ is computed and stored to be used in the next step by `models._ConcentrationModelBase._normed_concentration_cached()`. 
To inspect the properties of $\frac{C_{\mathrm{LR}}(t_i, D)}{\mathrm{vR(D)}}$ by finding its solution to the differential equation

$C_{\mathrm{LR}}(t_{i+1}, D)= \frac{\mathrm{vR(D)}\,N_{\mathrm{inf},i+1}}{\lambda_{vRR,i+1}(D)\,V_r} - \left(\frac{\mathrm{vR(D)}\,N_{\mathrm{inf},i+1}}{\lambda_{vRR,i+1}(D)\,V_r}-C_{\mathrm{LR}}(t_i, D)\right) \exp{-\lambda_{vRR,i+1}(D)\cdot (t_{i+1}-t_i)}$. 

Lets first clarify the notation by setting $y_i =C_{\mathrm{LR}}(t_{i}, D)$, $B_{i+1}=\frac{\mathrm{vR(D)}\,N_{\mathrm{inf},i+1}}{\lambda_{vRR,i+1}(D)\,V_r}$, 
and $K_i = \exp{-\lambda_{vRR,i+1}(D)\cdot (t_{i+1}-t_i)}$. Note that we no longer assume that the number of infected and viral removal rate are time-independent: 
$B_i$ depends on $i$ because $N_{\mathrm{inf},i+1}$ and/or $\lambda_{vRR,i+1}(D)$ change with $i$. Using the new notation, we get

$y_{i+1}= B_{i+1} - (B_{i+1}-y_i) K_i \quad \Rightarrow \quad y_{i+1} = B_{i+1}(1-K_i)+K_i y_i$

yielding the solution

$y_i=y_0 \cdot \left(\prod_{j=0}^{i-1} K_j\right)+\sum_{m=0}^{i-1}B_{m+1}\cdot \left(\prod_{j=m+1}^{i-1} K_j\right)(1- K_m)$

Observing that 

$\prod_{j=n}^{i-1}K_j = \prod_{j=n}^{i-1}\exp{-\lambda_{vRR,j+1}(D)\cdot (t_{j+1}-t_j)} = \exp{ - \sum_{j=n}^{i-1} \lambda_{vRR,j+1}(D)\cdot(t_{j+1}-t_j)}$,

$t_0=0$, and $y_0=C_{\mathrm{LR}}(0, D)=C_0$ we obtain the solution 

$C_{\mathrm{LR}}(t_i, D)
=C_0 \cdot \left(\exp{ - \sum_{j=0}^{i-1} \lambda_{vRR,j+1}(D)\cdot(t_{j+1}-t_j)}\right)
+\sum_{m=0}^{i-1}
\frac{\mathrm{vR(D)}\,N_{\mathrm{inf},m+1}}{\lambda_{vRR,m+1}(D)\,V_r}
\cdot \left(\exp{ - \sum_{j=m+1}^{i-1} \lambda_{vRR,j+1}(D)\cdot(t_{j+1}-t_j)}\right)
\cdot \left(1- \exp{-\lambda_{vRR,m+1}(D)\cdot (t_{m+1}-t_m)}\right)$

Importantly, the viral emission $\mathrm{vR(D)}$ is constant so, assuming the initial viral concentration $C_0=0$, $\mathrm{vR(D)}$ is a linear factor of $C_{\mathrm{LR}}(t_i, D)$ for all $i$.
Therefore, we can always compute the normalized concentration at the last time step $\frac{C_{\mathrm{LR}}(t_i, D)}{\mathrm{vR(D)}}$ and $\mathrm{vR(D)}$ separately.

Inserting $C_{\mathrm{LR}}(t_i, D)$ into the solution of the mass-balance ODE above, and replacing $N_{\mathrm{inf}}$ and $\lambda_{vRR}$ by $N_{\mathrm{inf},i+1}$ and $\lambda_{vRR,i+1}$, 
we find an expression for the long range viral concentration that does not require recurrent computations of $C_{\mathrm{LR}}(t_i, D)$.
The expression will, however, depend on all the stepwise constant values of the number of infected and viral removal rate.
Computationally, it might be just as efficient to compute $C_{\mathrm{LR}}(t_i, D)$ recurrently, as in CAiMIRA, because we also want to compute the concentration profile.

#### Computation of the Long-Range Concentration
For computational speed-up purposes we first compute $\frac{C_{\mathrm{LR}}(t, D)}{\mathrm{vR(D)}}$, i.e. the long-range concentration normalized by the emission rate. This diameter-dependent component is later retrieved in `models.ExposureModel` to compute the dose exposure.

Intermediate results for the long-range viral concentration can be obtained by computing

* The normalized concentration $\frac{C_{\mathrm{LR}}(t, D)}{\mathrm{vR(D)}}$ in `models._ConcentrationModelBase._normed_concentration()`.
* The normalization factor $\frac{\mathrm{vR(D)}}{\mathrm{p}_D(D)}$ in `models._PopulationWithVirus.emission_rate_per_person_when_present()`, which is called in `models.ConcentrationModel.normalization_factor()` to override the abstract method `models._ConcentrationModelBase.normalization_factor()`.
* $\frac{C_{\mathrm{LR}}(t, D)}{\mathrm{p}_D(D)}$ as the product of the two above methods in `models._ConcentrationModelBase.concentration()`.

Averaging the array $\left[\frac{C_{\mathrm{LR}}(t, D_1)}{\mathrm{p}_D(D_1)}, \frac{C_{\mathrm{LR}}(t, D_2)}{\mathrm{p}_D(D_2)}, ..., \frac{C_{\mathrm{LR}}(t, D_S)}{\mathrm{p}_D(D_S)}\right]$ returned by `models._ConcentrationModelBase.concentration()` corresponds to Monte Carlo integrating

$C_{\mathrm{LR}}^{\mathrm{total}}(t) = \int_{D_{\mathrm{min}}}^{D_{\mathrm{max}}} C_{\mathrm{LR}}(t, D) \mathrm{d}D$.

For the calculator app report, the total concentration (MC integral over the diameter) is performed only when generating the plot.
Otherwise, the diameter-dependence continues until we compute the inhaled dose in the `models.ExposureModel` class.

#### Dynamic occupancy
The mass-balance equation above assumes the emission rate $\mathrm{vR(D)}$ is the same for all the $N_{\mathrm{inf}}$ infected. Different infected may, however, have different physical activities, expirational activities, face mask, immunity, and presence. Concequently, the viral emission rate $\mathrm{vR(D)}$ and the probability distribution of the particle diameter $\mathrm{p}_{D}(D)$ are not the same for every infected. Lets assume we have $n_p$ different populations of infected, each with $N_{\mathrm{inf},n}$ infected with emission rate $\mathrm{vR}_n(D)$ and particle diameters sampled from $\mathrm{p}_{D,n}(D)$. Then, the mass balance equation describing the evolution of the viral concentration becomes

$\frac{\partial C_{\mathrm{LR}}(t, D)}{\partial t} = \frac{\sum_{n=1}^{n_p}\mathrm{vR}_n(D)\,N_{\mathrm{inf},n}}{V_r} - \lambda_{vRR}(D) \cdot C_{\mathrm{LR}}(t, D).$

Using the exact same procedure and assumptions as for the previous ODE, we find the solution to be

$C_{\mathrm{LR}}(t, D) = \frac{\sum_{n=1}^{n_p}\mathrm{vR}_n(D)\,N_{\mathrm{inf},n}}{\lambda_{vRR}(D)\,V_r} \cdot \left(1-\exp{-\lambda_{vRR}(D)\cdot t}\right)
=\sum_{n=1}^{n_p}\frac{\mathrm{vR}_n(D)\,N_{\mathrm{inf},n}}{\lambda_{vRR}(D)\,V_r} \cdot \left(1-\exp{-\lambda_{vRR}(D)\cdot t}\right) =\sum_{n=1}^{n_p}C_{\mathrm{LR},n}(t, D)$.

For the final equality, we set $C_{\mathrm{LR},n}(t, D)=\frac{\mathrm{vR}_n(D)\,N_{\mathrm{inf},n}}{\lambda_{vRR}(D)\,V_r} \cdot \left(1-\exp{-\lambda_{vRR}(D)\cdot t}\right)$ to indicate that this expression can be computed by a **ConcentrationModel** object, as described above, because all the $N_{\mathrm{inf},n}$ infected belong to the same **IntectedPopulation**, and thus have the same viral emission rate and samples of $D$. 
In CAiMIRA, we do indeed use different **ConcentrationModel** objects to compute the total long-range concentration resulting from emissions from infected with different properties 
(combined, together with the short-range concentration, in `models.ExposureModel.concentration()`). Using several **ConcentrationModel** objects was motivated by the **InfectedPopulation** objects having different samples of $D$ stored in their **Exporation** object, which cannot be considered equal because they stem from different distributions $\mathrm{p}_{D,n}(D)$. 
When we Monte Carlo integrate, we compute

$C_{\mathrm{LR}}^{\mathrm{total}}(t) = \int_{D_{\mathrm{min}}}^{D_{\mathrm{max}}} C_{\mathrm{LR}}(t, D) \mathrm{d}D $

$= \sum_{n=1}^{n_p} \int_{D_{\mathrm{min}}}^{D_{\mathrm{max}}} \frac{C_{\mathrm{LR},n}(t, D)}{\mathrm{p}_{D,n}(D)} \cdot \mathrm{p}_{D,n}(D) \mathrm{d}D$

$ \approx \sum_{n=1}^{n_p} \frac{1}{S_n}\sum_{i=1}^{S_n} \frac{C_{\mathrm{LR},n}(t, D_{n,i})}{\mathrm{p}_{D,n}(D_{n,i})}$.


### Short-Range Compartment
#### Derivation of the Analytical Short-Range Concentration
The viral concentration at short-range is the result of a two-stage exhaled jet model developed by Jia, W. et al. <sup>[1](#id7)</sup> and is expressed as:

$C_{\mathrm{SR}}(t, D) 
= C_{\mathrm{LR}} (t, D) + \frac{1}{S({x})} \cdot (C_{0, \mathrm{SR}}(D) - C_{\mathrm{LR}}(t, D))$,

where $S(x) > 0$ is the dilution factor due to jet dynamics, as a function of the interpersonal distance $x$, and 

$C_{0, \mathrm{SR}}(D) = \mathrm{vl_{in}} \cdot f_{\mathrm{inf}} \cdot E_c(D)$

is the initial concentration of virions at the mouth/nose outlet during exhalation. Note that $C_{0, \mathrm{SR}}(D)$ is constant over time, except it is set to zero untill (and including) the the start of the short-range interaction and after the end of the short-range interaction.

We allow the physical and expirational activity of the infected and exposed to be different at short-range and long-range (in the current frontent, only the expirational activity may be different).
Also, because smaller particles remain airborn longer than bigger particles, we set $D_{\mathrm{max}}=20\mathrm{μm}$ at long-range and $D_{\mathrm{min}}=100\mathrm{μm}$ at short-range.
Concequently, $E_c(D)$ has a different $N_p$ for $C_{0, \mathrm{SR}}(D)$ than for $C_{\mathrm{LR}} (t, D)$, so the particle diameters sampled to compute $C_{0, \mathrm{SR}}(D)$ and $C_{\mathrm{LR}} (t, D)$ are drawn from different probability distributions. 
Lets name the different probability distributions at long-range and short-range $\mathrm{p}_{\mathrm{LR},D}(D)$ and $\mathrm{p}_{\mathrm{SR},D}(D)$.

In CAiMIRA version 4.18.0, we sample the diameters from the different $\mathrm{p}_{\mathrm{LR},D}(D)$ and $\mathrm{p}_{\mathrm{SR},D}(D)$, compute $\frac{C_{\mathrm{LR}}(t, D_i)}{\mathrm{p}_{\mathrm{LR},D}(D_i)}$ and $\frac{C_{0, \mathrm{SR}}(D_j)}{\mathrm{p}_{\mathrm{SR},D}(D_j)}$,
and interpolate the vector $\left[\frac{C_{\mathrm{LR}}(t, D_1)}{\mathrm{p}_{\mathrm{LR},D}(D_1)}, \frac{C_{\mathrm{LR}}(t, D_2)}{\mathrm{p}_{\mathrm{LR},D}(D_2)}, ..., \frac{C_{\mathrm{LR}}(t, D_{S_N})}{\mathrm{p}_{\mathrm{LR},D}(D_{S_N})}\right]$ 
to the diameter basis sampled from $\mathrm{p}_{\mathrm{SR},D}(D)$. Thechnically, we then Monte Carlo Integrate

$C_{\mathrm{SR}}^{\mathrm{total}}(t) 
= \int_{D_\mathrm{min}}^{D_\mathrm{max}} C_{\mathrm{SR}}(t, D) \mathrm{d}D 
= \int_{D_\mathrm{min}}^{D_\mathrm{max}} C_{\mathrm{LR}} (t, D) + \frac{1}{S({x})} \cdot (C_{0, \mathrm{SR}}(D) - C_{\mathrm{LR}}(t, D)) \mathrm{d}D $

$ \approx \int_{0}^{100\mathrm{μm}} \frac{C_{\mathrm{LR}}(t, D)}{\mathrm{p}_{\mathrm{LR},D}(D)} + \frac{1}{S({x})} \left( \frac{C_{0, \mathrm{SR}}(D) }{\mathrm{p}_{\mathrm{SR},D}(D)} -\frac{C_{\mathrm{LR}}(t, D)}{\mathrm{p}_{\mathrm{LR},D}(D)}\right) \mathrm{p}_{\mathrm{SR},D}(D) \mathrm{d}D$

which is a good approximation if $\mathrm{p}_{\mathrm{LR},D}(D) \approx \mathrm{p}_{\mathrm{SR},D}(D)$ and $\mathrm{p}_{\mathrm{LR},D}(D_i) \approx 0$ for $D_i > 20\mathrm{μm}$.
In the newer versions of CAiMIRA, however, we aviod the approximation by rather computing

$C_{\mathrm{SR}}^{\mathrm{total}}(t) 
= \int_{D_\mathrm{min}}^{D_\mathrm{max}} C_{\mathrm{SR}}(t, D) \mathrm{d}D 
= \int_{D_\mathrm{min}}^{D_\mathrm{max}} C_{\mathrm{LR}}(t, D) + \frac{1}{S({x})} \left(C_{0, \mathrm{SR}}(D) - C_{\mathrm{LR}}(t, D) \right) \mathrm{d}D $

$= \int_{0}^{20\mathrm{μm}} \frac{C_{\mathrm{LR}}(t, D)}{\mathrm{p}_{\mathrm{LR},D}(D)} \cdot \mathrm{p}_{\mathrm{LR},D}(D) \mathrm{d}D + \frac{1}{S({x})} \cdot \left(\int_{0}^{100\mathrm{μm}} \frac{C_{0, \mathrm{SR}}(D) }{\mathrm{p}_{\mathrm{SR},D}(D)} \cdot \mathrm{p}_{\mathrm{SR},D}(D) \mathrm{d}D- \int_{0}^{20\mathrm{μm}} \frac{C_{\mathrm{LR}}(t, D)}{\mathrm{p}_{\mathrm{LR},D}(D)} \cdot \mathrm{p}_{\mathrm{LR},D}(D) \mathrm{d}D \right)$

$\approx \frac{1}{S_N}\sum_{i=1}^{S_N} \frac{C_{\mathrm{LR}}(t, D_i)}{\mathrm{p}_{\mathrm{LR},D}(D_i)} + \frac{1}{S({x})} \cdot \left(\frac{1}{S_N}\sum_{j=1}^{S_N} \frac{C_{0, \mathrm{SR}}(D_j)}{\mathrm{p}_{\mathrm{SR},D}(D_j)} - \frac{1}{S_N}\sum_{i=1}^{S_N} \frac{C_{\mathrm{LR}}(t, D_i)}{\mathrm{p}_{\mathrm{LR},D}(D_i)} \right)$.

Note that $C_{\mathrm{SR}}(t, D)$ is the actual concentration at short-range, with the long-range concentration entrained. Hence, one is NOT supposed to add the long-range and short-range concentration on top of each other.
To ease addition of contributions from several, incremental short-range interactions, we define the short-range concentration difference

$C_{\mathrm{SR-LR}}^{\mathrm{total}}(t) = C_{\mathrm{SR}}^{\mathrm{total}}(t) - C_{\mathrm{LR}}^{\mathrm{total}}(t)$

$ = \frac{1}{S({x})} \cdot \left(\int_{0}^{100\mathrm{μm}} \frac{C_{0, \mathrm{SR}}(D) }{\mathrm{p}_{\mathrm{SR},D}(D)} \cdot \mathrm{p}_{\mathrm{SR},D}(D) \mathrm{d}D- \int_{0}^{20\mathrm{μm}} \frac{C_{\mathrm{LR}}(t, D)}{\mathrm{p}_{\mathrm{LR},D}(D)} \cdot \mathrm{p}_{\mathrm{LR},D}(D) \mathrm{d}D \right) $

$\approx \frac{1}{S({x})} \cdot \left(\frac{1}{S_N}\sum_{j=1}^{S_N} \frac{C_{0, \mathrm{SR}}(D_j)}{\mathrm{p}_{\mathrm{SR},D}(D_j)} - \frac{1}{S_N}\sum_{i=1}^{S_N} \frac{C_{\mathrm{LR}}(t, D_i)}{\mathrm{p}_{\mathrm{LR},D}(D_i)} \right)$

For the sake of curiosity, note that that if $S({x}) < \infty$ and $C_{0, \mathrm{SR}}(D)$ is small enough (e.g. zero) then $C_{\mathrm{SR-LR}}^{\mathrm{total}}(t) < 0$, 
meaning the exhaled jet of a person with a low (or no) viable viral load and/or emission rate contains less virions than the background concentration. 
In the CAiMIRA model, only the short-range concentration from infectious are modeled, and it seems probable that every infected population has $C_{0, \mathrm{SR}}(D)$ is big enough for $C_{\mathrm{SR-LR}}^{\mathrm{total}}(t) > 0$.

#### The Dilution Factor
This **dilution factor** is given by 
$$
S({x}) =
\begin{cases} 
\frac{2𝛽_{r,j}(x+x_{0}}{D_m} \hspace{2cm} 0 < x \leq x^*,\\
S({x^*})[1+\frac{𝛽_{r,p}(x-x^*)}{𝛽_{r,j}(x+x_{0})}]^3 \quad x > x^*,
\end{cases}
$$

where $x_{0}=\frac{D_m}{2𝛽_{\mathrm{r1}}}$ distance of the virtual origin of the puff-like stage (in $\mathrm{m}$) with $D_m$ being the diameter (in $\mathrm{m}$) of the mouth opening, assumed to be a perfect circle.
All the $𝛽$-parameters are streamwise and radial penetration coefficients set in `caimira.calculator.store.data_registry`.
The distance $x$ a random variable sampled from a log-normal distribution in `monte_carlo.data.short_range_distances()` and passed as `distance` to `models.ShortRangeModel`. 
The transition point is defined as 

$\mathrm{x^*}=𝛽_{\mathrm{x1}} \cdot \sqrt[4]{Q_{\mathrm{exh}} \cdot u_{0}} \cdot \sqrt{\mathrm{t^*} + t_{0}} - x_{0}$,

where $Q_{\mathrm{exh}}= φ \mathrm{BR}_{\mathrm{k}}$ is the expired flow rate during the expiration period in $\mathrm{m^{3} s^{-1}}$. 
$φ$ is the (dimensionless) exhalation coefficient, given by the ratio between the total period of a breathing cycle and the duration of the exhalation alone. 
Assuming the duration of an inhalation and an exhalation are equal, and one starts immediately after the other, $φ=2$. 
$\mathrm{BR}_{\mathrm{k}}$ is the breathing rate determined by the infected's physical activity during the short-range interaction.
Next, $u_{0}=\frac{Q_{\mathrm{exh}}}{A_{m}}$ is the expired jet speed (in $\mathrm{m s^{-1}}$), with $A_{m}$ being the area of the mouth opening.
The time of the transition point $\mathrm{t^*}$ is defined as half a breathing cycle, corresponding to the end of the exhalation period when the jet is interrupted, and set in `caimira.calculator.store.data_registry`.
Finally, $t_{0} = \frac{\sqrt{\pi} \cdot D_m^3}{8𝛽_{\mathrm{r1}}^2𝛽_{\mathrm{x1}}^2Q_{exh}}$ is the time (in $\mathrm{s}$) corresponding to the distance of the virtual origin of the puff-like stage $x_{0}$.


#### Computation of the Short-Range Concentration
`models.ShortRangeModel` models the short-range component of the short-range concentration and the **dilution_factor**. 
Its inputs of`models.ShortRangeModel` are the **infected** population expiering the jet, their **expiration**, their physical **activity**, the **presence time** for the short-range interaction, and the **interpersonal distance** between any the infected and the exposed they are breathing at.
Note that **infected** is an instance of `models.InfectedPopulation`, which also contains instances of **Expiration** and **Activity**. However, these correspond to the expirational activities and physical activities of the infected during long-range interactions, which may be different from the expiration and activity during short-range interactions.
Therefore, we generate new **Expiration** and **Activity** objects for **ShortRangeModel** corresponding to the infecteds' behaviour at short range. 
Even if the expirational activities at long-range and short-range are the same, a new **Expiration** instance is needed at short-range because $D_{\mathrm{max}}$ is different at short-range and long-range, yielding **Expiration** objects with different diameter samples. 
`models.ShortRangeModel` is kept completely seperate of `models._ConcentrationModelBase`, exce

Similarly to the computation of the long-range concentration in `models._ConcentrationModelBase`, we separate the computation of diameter-dependent random variables and diameter-independent random variables for computational efficiency. 
We compute
* the normalized viral concentration at the outlet, i.e. $\frac{C_{0, \mathrm{SR}}(D)}{E_c(D)}=\mathrm{vl_{in}} \cdot f_{\mathrm{inf}}$, in `models.ShortRangeModel._normed_jet_origin_concentration()` 
* the dilution factor $\frac{1}{S({x})}$ in `models.ShortRangeModel.dilution_factor()` 
* the normalization factor $\frac{E_c(D)}{\mathrm{p}_{\mathrm{SR},D}(D)}$ in `models.ShortRangeModel.normalization_factor()`.

The product of the two first methods are returned by `models.ShortRangeModel._normed_jet_origin_concentration()` and sendt to **ExposureModel**, 
keeping the diameter dependence and separation of random variables because more diameter-dependent variables will be introduced before Monte Carlo integrating to compute the dose exposure. 

If we want intermediate results for the full short-range concentration, e.g. for the report, we integrate the long-range and short-range components over the particle diameter before adding them together. 
$C_{\mathrm{SR-LR}}^{\mathrm{total}}(t)$ is computed in `models.ShortRangeModel.short_range_concentration_difference()` and added to $C_{\mathrm{LR}}^{\mathrm{total}}(t)$ from `models.ConcentrationModel.concentration()` to compute $C_{\mathrm{SR}}^{\mathrm{total}}(t)$, as explained above. 
Note that `models.ShortRangeModel` is kept completely seperate of `models._ConcentrationModelBase` untill
untill an instance of `models.ConcentrationModel` is passed to, and combined with, `models.ShortRangeModel.short_range_concentration_difference()` to compute $C_{\mathrm{SR}}^{\mathrm{total}}(t)$ [MR TODO].

Note that multiple short-range interactions can be defined during a given exposure time. We initialize one **ShortRangeModel** for each interaction.

### Total Viral Concentration
Different exposed populations may experience different viral concentrations depending on their occupancy periods and the occurrence of short-range interactions. For a given exposed population, the total viral concentration at time $t$ is given by

$C^{\mathrm{total}}(t) = \mathbf{1}_{t \in T}(t) \cdot C_{\mathrm{LR}}^{\mathrm{total}}(t) + \sum_{i}^{n_\mathrm{SR}}\mathbf{1}_{t \in T_{\mathrm{SR},i}}(t) \cdot C_{\mathrm{SR-LR},i}^{\mathrm{total}}(t)$

where $n_\mathrm{SR}$ denotes the total number of short-range interactions experienced by the exposed population during its entire occupancy period. The indicator function

$
\mathbf{1}_{t \in T}(t) =
\begin{cases}
1, & \text{if } t \in T, \\
0, & \text{else}
\end{cases}
$

ensures the long-range concentration is only considered for the set of times $T$ when the exposed is inside the room, which is a subset of the time interval $[t_0, t_n]$ from when the exposed first enters at $t_0$ untill they leave for the last time at $t_n$. Similarly, the indicator function associated with the $i$-th short-range interaction is defined as

$
\mathbf{1}_{t \in T_{\mathrm{SR},i}}(t) =
\begin{cases}
1, & \text{if } t \in T_{\mathrm{SR},i}, \\
0, & \text{else},
\end{cases}
$

where $T_{\mathrm{SR},i} \subseteq T$ is the set of times when the $i$-th short-range interaction occurs. Thus, the contribution $C_{\mathrm{SR-LR},i}^{\mathrm{total}}(t)$ is included in the total concentration only while that short-range interaction is happening. Note, as previously mentioned, that we integrate over the particle diameter before summing together the long-range and short-range contributions to the concentration because we have different probability distributions for the particle diameter at long-range and short-range. For each exposed population, $C^{\mathrm{total}}(t)$ is computed by `models.ExposureModel.concentration()`. 

In addition to the viral concentration profile for each exposed population, we have the long-range viral concentration profile which is independent of all the exposed populations. This long-range concentration is computed by `models._ConcentrationModelBase.concentration()`, and also retrieved by `models.ExposureModel.concentration()` for an **ExposureModel** with no short-range interactions.

The viral concentration at long-range and from the perspective of a specific exposed population is plotted over time in the report.


## Dose
The diameter-dependent viral dose deposited in the respiratory tract of an exposed is given by

$\mathrm{vD}(D) = \int_{t_0}^{t_n}C(t, D)\;\ {d}t \cdot \mathrm{BR}_{\mathrm{k}} \cdot f_{\mathrm{dep}}(D) \cdot (1-\eta_{\mathrm{in}})$,

where $t_0$ is the first time exposed enters and $t_n$ is the last time they leave. $\mathrm{BR}_{\mathrm{k}}$ is the breathing rate of the exposed, $f_{\mathrm{dep}}(D)$ is the deposition factor in the respiratory tract, and $\eta_{\mathrm{in}}$ is the inwards mask efficiency of the face mask worn by the exposed.
$C(t, D)$ is the viral concentration from the perspective of the exposed. 
When the exposed is inside the room and not engaged in a short-range interaction $C(t, D)=C_{\mathrm{LR}} (t, D)$, 
and when the exposed is enganging in their $i$-th short-range interaction $C(t, D)=C_{\mathrm{SR},i} (t, D)$. Using the definition of , this can be expressed as

$C(t, D) = \mathbf{1}_{t \in T}(t) \cdot C_{\mathrm{LR}} (t, D) + \sum_{i}^{n_\mathrm{SR}}\mathbf{1}_{t \in T_{\mathrm{SR},i}}(t) \cdot C_{\mathrm{SR-LR},i} (t, D)$

where the indicator functions ant the time intervals $T$ and $T_{\mathrm{SR},i}$ follow the definitions from the previous sections. We have now introduced all diameter-dependent quantities, and all down-stream computations only depend on the total dose exposure

$\mathrm{vD}^{\mathrm{total}} =\int_{\mathrm{D_{min}}}^{\mathrm{D_{max}}} \mathrm{vD}(D) \mathrm{d}D$.

Similarly to the computation of the total viral concentration, we account for having diferent diameter distributions at long-range and short-range when Monte Carlo integrating $C(t, D)$ over $D$ by separating the dose into a long-range and a short-range component as follows

$\mathrm{vD}^{\mathrm{total}} 
=\int_{\mathrm{D_{min}}}^{\mathrm{D_{max}}} \int_{t_0}^{t_n}C(t, D)\;\ {d}t \cdot \mathrm{BR}_{\mathrm{k}} \cdot f_{\mathrm{dep}}(D) \cdot (1-\eta_{\mathrm{in}}) \mathrm{d}D$

$\quad\quad\quad=\int_{\mathrm{D_{min}}}^{\mathrm{D_{max}}} \int_{t_0}^{t_n}\mathbf{1}_{t \in T}(t) \cdot C_{\mathrm{LR}} (t, D) \;\ {d}t \cdot \mathrm{BR}_{\mathrm{k}} \cdot f_{\mathrm{dep}}(D) \cdot (1-\eta_{\mathrm{in}}) \mathrm{d}D$

$\quad\quad\quad\quad+\sum_{i}^{n_\mathrm{SR}}\int_{\mathrm{D_{min}}}^{\mathrm{D_{max}}} \int_{t_0}^{t_n}\mathbf{1}_{t \in T_{\mathrm{SR},i}}(t) \cdot C_{\mathrm{SR-LR},i} (t, D) \;\ {d}t \cdot \mathrm{BR}_{\mathrm{k}} \cdot f_{\mathrm{dep}}(D) \cdot (1-\eta_{\mathrm{in}}) \mathrm{d}D$

Lets define

$\mathrm{vD}_{\mathrm{LR}}^{\mathrm{total}} =\int_{\mathrm{D_{min}}}^{\mathrm{D_{max}}} \int_{t_0}^{t_n}\mathbf{1}_{t \in T}(t) \cdot C_{\mathrm{LR}} (t, D) \;\ {d}t \cdot \mathrm{BR}_{\mathrm{k}} \cdot f_{\mathrm{dep}}(D) \cdot (1-\eta_{\mathrm{in}}) \mathrm{d}D$

$\mathrm{vD}_{\mathrm{SR-LR},i}^{\mathrm{total}}=\int_{\mathrm{D_{min}}}^{\mathrm{D_{max}}} \int_{t_0}^{t_n}\mathbf{1}_{t \in T_{\mathrm{SR},i}}(t) \cdot C_{\mathrm{SR-LR},i} (t, D) \;\ {d}t \cdot \mathrm{BR}_{\mathrm{k}} \cdot f_{\mathrm{dep}}(D) \cdot (1-\eta_{\mathrm{in}}) \mathrm{d}D$

so

$\mathrm{vD}^{\mathrm{total}} = \mathrm{vD}_{\mathrm{LR}}^{\mathrm{total}} + \sum_{i}^{n_\mathrm{SR}}\mathrm{vD}_{\mathrm{SR-LR},i}^{\mathrm{total}}$

This separation also makes it easier to compare the importance of long-range vs short-range interactions for viral transmission. 


#### Long-Range Dose
The long-range viral dose deposited in the respiratory tract of the exposed, for a given aerosol diameter, is

$\mathrm{vD}_{\mathrm{LR}}(D) = \int_{t1}^{t2}C_{\mathrm{LR}}(t, D)\;\mathrm{d}t \cdot \mathrm{BR}_{\mathrm{k}} \cdot f_{\mathrm{dep}}(D) \cdot (1-\eta_{\mathrm{in}})$

where $t_1$ and $t_n$ are the start and end times of the occupancy (and simulation), $C_{\mathrm{LR}}(t, D)$ is the long-range viral concentration, $\mathrm{BR}_{\mathrm{k}}$ is the breathing rate of the exposed, $f_{\mathrm{dep}}(D)$ is the deposition fraction in the respiratory tract, and  $\eta_{\mathrm{in}}$ is the inward mask efficiency. Over an interval $[t_i, t_{i+1}]$ where both $\lambda_{vRR}(t, D)$ and $N_{\mathrm{inf}}$ are constant, $C_{\mathrm{LR}}(t, D)$ is given by the solution to the mass-balance ODE above. Therefore, we compute 


$\int_{t_1}^{t_n} C_{\mathrm{LR}}(t, D) \mathrm{d}t  =  \sum_{i=1}^n \int_{t_i}^{t_{i+1}} C_{\mathrm{LR}}(t, D) \mathrm{d}t $
    
$= \sum_{i=1}^n \int_{t_i}^{t_{i+1}} \left[\mathrm{vR(D)} \cdot \left(\frac{N_{\mathrm{inf}}}{\lambda_{vRR}(D)\,V_r} - \left(\frac{N_{\mathrm{inf}}}{\lambda_{vRR}(D)\,V_r}- \frac{C_{\mathrm{LR},0}(D)}{\mathrm{vR(D)}} \right) \exp{-\lambda_{vRR}(D)\cdot t} \right) \right] \mathrm{d}t$

$=  \sum_{i=1}^n \frac{v_R(D)\,N_{inf}}{\lambda_{vRR}(D, t_i)\,V_r} (t_{i+1}-t_{i}) + \sum_{i=1}^n \left(\frac{v_R(D)\,N_{inf}}{\lambda_{vRR}(D, t_i)\,V_r}- C_{\mathrm{LR},0}(D)\right) \frac{\exp{-\lambda_{vRR}(D,t_i)t_{i+1}}}{\lambda_{vRR}(D,t_i)} - \sum_{i=1}^n \left(\frac{v_R(D)\,N_{inf}}{\lambda_{vRR}(D, t_i)\,V_r}- C_{\mathrm{LR},0}(D)\right) \frac{\exp{-\lambda_{vRR}(D,t_i)t_i}}{\lambda_{vRR}(D,t_i)}$

for a given particle diameter $D$. The total dose deposited in the respiratory tract of the exposed is obtained by integrating over the particle diameter, which we approximate by 

$\mathrm{vD}^{\mathrm{total}} =\int_{\mathrm{D_{min}}}^{\mathrm{D_{max}}} \mathrm{vD}(D) \mathrm{d}D$

cannot be solved analytically and is therefore solved using Monte Carlo integration.

#### Short-Range Dose

### 






The long-range concentration, integrated over the exposure time (in piecewise constant steps), $C(D)$, is given by `models._ConcentrationModelBase.integrated_concentration()`.

The following methods calculate the integrated concentration between two times. They are mostly used when calculating the **dose**:

* `models._ConcentrationModelBase.normed_integrated_concentration()`, $\mathrm{C_\mathrm{normed}}(D)$ that returns the integrated long-range concentration of viruses in the air, between any two times, normalized by the emission rate per person infected. Note that this method performs the integral between any two times of the previously mentioned `models._ConcentrationModelBase._normed_concentration()` method.
* `models._ConcentrationModelBase.integrated_concentration()`, $C(D)$, that returns the same result as the previous one, but multiplied by the emission rate (per person infected).

The integral over the exposure times is calculated directly in the class (integrated methods).






## Dose - vD

The term dose refers to the number of viable virions (infectious virus) that will contribute to a potential infection.
It results in a combination of several properties: exposure, inhalation rate, aerosol deposition in the respiratory tract and the effect of protective equipment such as masks.

The receiving dose, which is inhaled by the exposed host, in infectious virions per unit diameter (diameter-dependence),
is calculated by first integrating the viral concentration profile (for a given particle diameter) over the exposure time and multiplying by scaling factors such as the proportion of virions which are infectious and the deposition fraction,
as well as the inhalation rate and the effect of masks:

$\mathrm{vD}{\mathrm{LR}}(D) = \int_{t1}^{t2}C(t, D)\;\mathrm{d}t \cdot \mathrm{BR}_{\mathrm{k}} \cdot f_{\mathrm{dep}}(D) \cdot (1-\eta_{\mathrm{in}})$ .

where $C(t, D)$ is the concentration value at a given time, which can be either the short- or long-range concentration, $f_{\mathrm{dep}}(D)$ is the (diameter-dependent) deposition fraction in the respiratory tract, $\mathrm{BR}_{\mathrm{k}}$ is the inhalation rate and $\eta_{\mathrm{in}}$ is the inward efficiency of the face mask.

Given that the calculation is diameter-dependent, to calculate the dose in the model, the code contains different methods that consider the parameters that are dependent on the aerosol size, $D$.
The total dose, at the end of the exposure scenario, results from the sum of the dose accumulated over time, integrated over particle diameters:

$\mathrm{vD^{total}} = \int_0^{D_{\mathrm{max}}} \mathrm{vD}(D) \, \mathrm{d}D$ .

This calculation is computed using a Monte-Carlo integration over $D$. As previously described, many different parameters samples are generated using the probability distribution from the $N_p(D)$ equation.
The dose for each of them is then computed, and their **average** value over all samples represents a good approximation of the total dose, provided that the number of samples is large enough.

### Long-range approach

Regarding the concentration part of the long-range exposure (concentration integrated over time, $\int_{t1}^{t2}C_{\mathrm{LR}}(t, D)\;\mathrm{d}t$), the respective method is `models.ExposureModel._long_range_normed_exposure_between_bounds()`,
which uses the long-range exposure (concentration) between two bounds (time1 and time2), normalized by the emission rate of the infected population (per person infected), calculated from `models._ConcentrationModelBase.normed_integrated_concentration()`.
The former method filters out the given bounds considering the breaks through the day (i.e. the time intervals during which there is no exposition to the virus) and retrieves the integrated long-range concentration of viruses in the air between any two times.

After the calculations of the integrated concentration over the time, in order to calculate the final dose, we have to compute the remaining factors in the above equation.
Note that the **Monte-Carlo integration over the diameters is performed at this stage**, where all the diameter-dependent parameters are grouped together to calculate the final average (`np.mean()`).

Since, in the previous chapters, the quantities where normalised by the emission rate per person infected, one will need to re-incorporate it in the equations before performing the MC integrations over $D$.
For that we need to split $\mathrm{vR}(D)$ (`models._PopulationWithVirus.emission_rate_per_person_when_present()`) in diameter-dependent and diameter-independent quantities:

$\mathrm{vR}(D) = \mathrm{vR}(D-\mathrm{dependent}) \times \mathrm{vR}(D-\mathrm{independent})$

with

$\mathrm{vR}(D-\mathrm{dependent}) = \mathrm{cn} \cdot V_p(D) \cdot (1 − \mathrm{η_{out}}(D))$ - `models.InfectedPopulation.aerosols()`

$\mathrm{vR}(D-\mathrm{independent}) = \mathrm{vl_{in}} \cdot \mathrm{f_{inf}} \cdot \mathrm{BR_{k}}$ - `models.InfectedPopulation.emission_rate_per_aerosol_per_person_when_present()`

In other words, in the code the procedure is the following (all performed in `models.ExposureModel.long_range_deposited_exposure_between_bounds()` method):

* start re-incorporating the emission rate by first multiplying by the diameter-dependent quantities: $\mathrm{vD_{aerosol}}(D) = (\int_{t1}^{t2}C_{\mathrm{LR}}(t, D)\;\mathrm{d}t \cdot \mathrm{vR}(D-\mathrm{dependent}) \cdot f_{\mathrm{dep}}(D))$, in `models.ExposureModel.long_range_deposited_exposure_between_bounds()` method;
* perform the **MC integration over the diameters**, which is considered equivalent as the mean of the distribution if the sample size is large enough: $\mathrm{vD_{aerosol}} = \mathrm{np.mean}(\mathrm{vD_{aerosol}}(D))$;
* multiply the result with the remaining diameter-independent quantities of the emission rate used previously to normalize: $\mathrm{vD_{emission-rate}} = \mathrm{vD_{aerosol}} \cdot \mathrm{vR}(D-\mathrm{independent})$;
* in order to complete the equation, multiply by the remaining diameter-independent variables in $\mathrm{vD}$ to obtain the total value: $\mathrm{vD^{total}} = \mathrm{vD_{emission-rate}} \cdot \mathrm{BR}_{\mathrm{k}} \cdot (1-\eta_{\mathrm{in}})$;
* in the end, the dose is a vectorized float used in the probability of infection formula.

**Note**: The aerosol volume concentration (*aerosols*) is introduced because the integrated concentration over the time was previously normalized by the emission rate (per person).
Here, to calculate the integral over the diameters we also need to consider the diameter-dependent variables that are on the emission rate, represented by the aerosol volume concentration which depends on the diameter and on the mask type:

$\mathrm{aerosols} = \mathrm{cn} \cdot V_p(D) \cdot (1 − \mathrm{η_{out}}(D))$ .
The $\mathrm{cn}$ factor, which represents the total number of aerosols emitted, is introduced here as a scaling factor, as otherwise the Monte-Carlo integral would be normalized to 1 as the probability distribution.

**Note**: for simplification of the notations, here the dose corresponding exclusively to the long-range contribution is written as $\mathrm{vD_{LR}}(D)= \mathrm{vD}(D)$.

In the end, the governing method is `models.ExposureModel.deposited_exposure_between_bounds()`, in which the deposited_exposure is equal to long_range_deposited_exposure_between_bounds in the absence of short-range interactions.

### Short-range approach

In theory, the dose during a close-proximity interaction (short-range) is simply added to the dose inhaled due to the long-range and may be defined as follows:

$\mathrm{vD}(D)= \mathrm{vD^{LR}}(D) + \sum\limits_{i=1}^{n} \int_{t1}^{t2}C_{\mathrm{SR}}(t, D)\;\mathrm{d}t \cdot \mathrm{BR}_{\mathrm{k}} \cdot f_{\mathrm{dep}}(D) \cdot (1-\eta_{\mathrm{in}})$ ,

where $\mathrm{vD_{LR}}(D)$ is the long-range, diameter-dependent dose computed previously.

From above, the short-range concentration:

$C_{\mathrm{SR}}(t, D) = C_{\mathrm{LR}, 100μm} (t, D) + \frac{1}{S({x})} \cdot (C_{0, \mathrm{SR}}(D) - C_{\mathrm{LR}, 100μm}(t, D))$ ,

In the code, the method that returns the value for the total dose (independently if it is short- or long-range) is given by `models.ExposureModel.deposited_exposure_between_bounds()`.
For code simplification, we split the $C_{\mathrm{SR}}(t, D)$ equation into two components:

* short-range component: $\frac{1}{S({x})} \cdot (C_{0, \mathrm{SR}}(D) - C_{\mathrm{LR}, 100μm}(t, D))$;
* long-range component: $C_{\mathrm{LR}} (t, D)$.

Similarly as above, first we perform the multiplications by the diameter-dependent variables so that we can profit from the Monte-Carlo integration. Then we multiply the final value by the diameter-independent variables.
The method `models.ShortRangeModel._normed_jet_exposure_between_bounds()` gets the integrated short-range concentration of viruses in the air between the times start and stop, normalized by the **viral load** and **fraction of infectious virus**,
and excluding the **jet dilution** since it is also diameter-independent.
This corresponds to $C_{0, \mathrm{SR}}(D)$.

The method `models.ShortRangeModel._normed_interpolated_longrange_exposure_between_bounds()` retrieves the integrated short-range concentration due to the background concentration,
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

The final operation in the `models.ExposureModel.deposited_exposure_between_bounds()` accounts for the addition of the long-range component of the dose.

If short-range interactions exist: the long-range component is added to the already calculated short-range component (deposited_exposure), hence completing $C_{\mathrm{SR}}$.
If the are no short-range interactions: the short-range component (deposited_exposure) is zero, hence the result is equal solely to the long-range component $C_{\mathrm{LR}}$.


### Separation of Random Variables

It is important to distinguish between 1) Monte-Carlo random variables (which are vectorized independently on its diameter-dependence) and 2) numerical Monte-Carlo integration for the diameter-dependence.
Since the integral of the diameter-dependent variables are solved when computing the dose – $\mathrm{vD^{total}}$ – while performing some of the intermediate calculations,
we normalize the results by *dividing* by the Monte-Carlo variables that are diameter-independent, so that they are not considered in the Monte-Carlo integration (e.g. the **viral load** parameter, or the result of the `models.InfectedPopulation.emission_rate_per_aerosol_per_person_when_present()` method).


## Infection Probability
### Deterministic Exposure
#### Derivation
#### Implementation
### Probabilistic Exposure
#### Derivation
#### Implementation

## CO<sub>2</sub> Concentration

The estimate of the concentration of CO<sub>2</sub> in a given room to indicate the air quality is given by the same approach as for the long-range virus concentration,
$C_{\mathrm{LR}}(t, D)$, where $C_{\mathrm{LR},0}(D)$ is considered to be the background (outdoor) CO<sub>2</sub> concentration (`models.CO2ConcentrationModel.CO2_atmosphere_concentration()`).

In order to compute the CO<sub>2</sub> concentration one should then simply use the `models.CO2ConcentrationModel.concentration()` method.
A fraction of 4.2% of the exhalation rate of the defined activity was considered as supplied to the room (`models.CO2ConcentrationModel.CO2_fraction_exhaled()`).

Note still that nothing depends on the aerosol diameter $D$ in this case (no particles are involved) - hence in this class all parameters are constant w.r.t $D$.

Since the CO<sub>2</sub> concentration differs from the virus concentration, the specific removal rate, CO<sub>2</sub> atmospheric concentration and normalization factors are respectively defined in `models.CO2ConcentrationModel.removal_rate()`,
`models.CO2ConcentrationModel.min_background_concentration()` and `models.CO2ConcentrationModel.normalization_factor()`.

## References

* <a id='id7'>**[1]**</a> Jia, Wei, et al. “Exposure and respiratory infection risk via the short-range airborne route.” Building and environment 219 (2022): 109166. [doi.org/10.1016/j.buildenv.2022.109166](https://doi.org/10.1016/j.buildenv.2022.109166)
* <a id='id8'>**[2]**</a> Henriques, Andre, et al. “Modelling airborne transmission of SARS-CoV-2 using CARA: risk assessment for enclosed spaces.” Interface Focus 12.2 (2022): 20210076. [doi.org/10.1098/rsfs.2021.0076](https://doi.org/10.1098/rsfs.2021.0076)
