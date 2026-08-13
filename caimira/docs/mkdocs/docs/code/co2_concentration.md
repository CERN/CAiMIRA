# Computation of the CO<sub>2</sub> Concentration
In the following, `data_registry` refers to `caimira.calculator.store.data_registry` and `models` refers to `caimira.calculator.models.models.py`.

Similarly to the viral concentration, the CO<sub>2</sub> concentration is derived using mass balance. Every occupant emits CO<sub>2</sub> with emission rate proportional to their breathing (expiration) rate and fraction of CO<sub>2</sub> in expired breath $f_{CO_2}$. We assume $f_{CO_2}$ is constant (set to $4.2\%$ in `data_registry`) while the breating rate might vary between each population of occupants, depending on their physical activity. Let $\mathrm{BR}_{\mathrm{out},n}$ denote the breathing rate of the $n$-th population consisting of $N_n$ occupants, and let $n_p$ be the total number of different populations in the room. Ventilation $\lambda_{ACH}(t)$ is the only sink of CO<sub>2</sub>, and the background concentration $C_{out}$ is set to 440 ppm. Hence, the rate of change of the CO<sub>2</sub> concentration is given by the mass balance ODE

$$
\begin{equation*}
\frac{\mathrm{d}C_{CO_2}(t)}{\mathrm{d}t}
=
\frac{f_{CO_2} \cdot \sum_{n=1}^{n_p}\mathrm{BR}_{\mathrm{out},n} \cdot N_n}{V_r}
-
\lambda_{ACH}(t)\cdot \left(C_{CO_2}(t)-C_{\mathrm{out}}\right).
\end{equation*}
$$

Note that any human occupant is an emitter of CO<sub>2</sub>. Therefore, we do not have a similar segregation of *infected* and *exposed* populations as for viral transmission (see **[Viral Transmission](./viral_transmission.md)**). We only group the occupants into *populations* with different emission rates, i.e. different breathing rates and presence times, so that every member of the same *population* has the same (constant) breathing rate and present times.

Similar as for the viral concentration (see **[Viral Transmission](./viral_transmission.md)**), we can solve the ODE above over time intervals $[t_i, t_{i+1}]$ where the CO<sub>2</sub> concentration is the only time-dependent variable. This is achieved by assuming the ventilation is stepwise constant and defining $[t_i, t_{i+1}]$ so $\lambda_{ACH}(t)=\lambda_{ACH}(t_i)$ is constant. Using the same standard techniques for solving ODEs as for the viral concentration (see **[Viral Transmission](./viral_transmission.md)**), we get that the solution for $\forall t \in [t_i, t_{i+1}]$ is

$$
\begin{align*}
C_{CO_2}(t)
&=
C_{\mathrm{out}}+(C_{CO_2}(t_i)-C_{\mathrm{out}}) \cdot \exp(-\lambda_{ACH}(t_i)\cdot(t-t_i))\\
& \quad+\frac{f_{CO_2} \cdot \sum_{n=1}^{n_p}\mathrm{BR}_{\mathrm{out},n} \cdot N_n}{V_r\lambda_{ACH}(t_i)}\cdot (1-\exp(-\lambda_{ACH}(t_i)\cdot(t-t_i)))
\end{align*}
$$

where is $C_{CO_2,t_i}$ is the CO<sub>2</sub> concentration carried forward from the end of the previous time interval. Similar to the viral concentration, we observe that 

$$
\begin{align*}
C_{CO_2,n}(t)
&=
C_{CO_2,n}(t_i) \cdot \exp(-\lambda_{ACH}(t_i)\cdot(t-t_i))+\frac{f_{CO_2} \cdot \mathrm{BR}_{\mathrm{out},n} \cdot N_n}{V_r\lambda_{ACH}(t_i)}\cdot (1-\exp(-\lambda_{ACH}(t_i)\cdot(t-t_i)))
\end{align*}
$$

is the CO<sub>2</sub> concentration *increase* from $C_{\mathrm{out}}$ resulting from the presence of the $n$-th population only. We assume that the concentration starts at $C_{\mathrm{out}}$, i.e. $C_{CO_2}(t_0) = C_{\mathrm{out}}$. 
It follows by induction that

$$
\begin{align*}
C_{CO_2}(t)
&=
C_{\mathrm{out}}+\sum_{n=1}^{n_p}C_{CO_2,n}(t).
\end{align*}
$$



The CO<sub>2</sub> concentration is computed in much the same way as the viral concentration: We approximate the expected total concentration $C_{CO_2}(t)$ in `models.TotalCO2ConcentrationModel.concentration()`, separating the computations into $n_p$ `models.CO2ConcentrationModel` instances which each compute $C_{CO_2,n}(t)$ for the $n$-th population and then adding $C_{\mathrm{out}}$ at the end when summizing all the contributions. Similarly to `models.TotalViralConcentrationModel`, `models.TotalCO2ConcentrationModel` is a subclass of `models._TotalConcentrationModelBase`. Similarly to `models.ConcentrationModel` (computing the viral concentration for a single population), `models.CO2ConcentrationModel` is a subclass of `models._ConcentrationModelBase`. 

The essentail difference between `models.CO2ConcentrationModel` and `models.ConcentrationModel` are the emission rate, implemented in the respective normalization factors, and the removal rate. When computing the concentration in `models._ConcentrationModelBase`, we first normalize by the emission rate per person. For the CO<sub>2</sub> concentration, the emission rate per person is $f_{CO_2} \cdot \sum_{n=1}^{n_p}\mathrm{BR}_{\mathrm{out},n}$. 
Using induction, we can prove that $f_{CO_2} \cdot \mathrm{BR}_{\mathrm{out},n}$ always is a linear factor of $C_{CO_2,n}(t)$ as long as $C_{CO_2,n}(t_0)=0$, and so we use `models._ConcentrationModelBase._normed_concentration()` to compute the normalized CO<sub>2</sub> concentration $\frac{{CO_2,n}(t)}{f_{CO_2} \cdot \mathrm{BR}_{\mathrm{out},n}}$. We then specify `models.CO2ConcentrationModel.normalization_factor()` as $f_{CO_2} \cdot \mathrm{BR}_{\mathrm{out},n}$. 

The expected CO<sub>2</sub> concentration increase $C_{CO_2,n}(t)$ is computed by Monte Carlo sampling $\mathrm{BR}_{\mathrm{out},n}$. The total expected CO<sub>2</sub> concentration is then

$$
\begin{align*}
E[C_{CO_2}(t)]
&=
C_{\mathrm{out}}+\sum_{n=1}^{n_p}E[C_{CO_2,n}(t)]\\
&\approx
C_{\mathrm{out}}+\sum_{n=1}^{n_p}\frac{1}{S}\sum_{i=1}^{S}
\left[C_{CO_2,n}(t_i) \cdot \exp(-\lambda_{ACH}(t_i)\cdot(t-t_i))+\frac{f_{CO_2} \cdot \mathrm{BR}_{\mathrm{out},n,i} \cdot N_n}{V_r\lambda_{ACH}(t_i)}\cdot (1-\exp(-\lambda_{ACH}(t_i)\cdot(t-t_i)))\right]\\
\end{align*}
$$

Note that it is neccecary to complete the Monte Carlo approximation of the expected value of $C_{CO_2,n}(t)$ from each `models.CO2ConcentrationModel` before summizing the contributions from different `models.CO2ConcentrationModel` instances because the parameterization of the distributions $\mathrm{BR}_{\mathrm{out},n}$ is sampled from vary with $n$. 


## Expected CO<sub>2</sub> Concentration
NOTE: This is not currently implemented in CAiMIRA.

We could actually avoid Monte Carlo sampling when computing the expected CO<sub>2</sub> concentration because the CO<sub>2</sub> concentration is only linearly dependent on random variables $\mathrm{BR}_{\mathrm{out},n}$. To see this, note that the expected CO<sub>2</sub> concentration is given by

$$
\begin{align*}
E[C_{CO_2}(t)]
&=
C_{\mathrm{out}}+(C_{CO_2}(t_i)-C_{\mathrm{out}}) \cdot \exp(-\lambda_{ACH}(t_i)\cdot(t-t_i))\\
& \quad+\frac{f_{CO_2} \cdot \sum_{n=1}^{n_p}E[\mathrm{BR}_{\mathrm{out},n}] \cdot N_n}{V_r\lambda_{ACH}(t_i)}\cdot (1-\exp(-\lambda_{ACH}(t_i)\cdot(t-t_i)))
\end{align*}
$$

because $\mathrm{BR}_{\mathrm{out},n}$ is a linear component of the concentration. $\mathrm{BR}_{\mathrm{out},n}$ is log-normally distributed with expected value

$$
\begin{equation*}
E[\mathrm{BR}_{\mathrm{out},n}]
=
\exp\!\left(\mu_n+\frac{\sigma_n^2}{2}\right),
\end{equation*}
$$

where $\mu_n$ and $\sigma_n$ are the mean and standard deviation, respectively, of the log-normal distribution of $\mathrm{BR}_{\mathrm{out},n}$. Therefore, we could compute $E[C_{CO_2}(t)]$ completely deterministically. Similarly, we could also compute the variance of the CO<sub>2</sub> concentration deterministically as

$$
\begin{align*}
Var[C_{CO_2}(t)]
&=
\left(\frac{(N_{inf}+N_{exp}) \cdot f_{CO_2}}{V_r\lambda_{ACH}(t_i)}\right)^2\cdot Var[\mathrm{BR}_{\mathrm{out},n}] \cdot(1-\exp(-\lambda_{ACH}(t_i)\cdot(t-t_i)))^2
\end{align*}
$$

where 

$$
\begin{equation*}
Var[\mathrm{BR}_{\mathrm{out},n}]
=
\left(1-\exp\!\left(\sigma_n^2\right)\right)\exp\!\left(2\mu_n+\sigma_n^2\right),
\end{equation*}
$$

is the variance of the log-normally distributed breathing rate $\mathrm{BR}_{\mathrm{out},n}$.