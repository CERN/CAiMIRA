# Computation of the CO<sub>2</sub> Concentration
Similarly to the viral concentration, the CO<sub>2</sub> concentration is derived using mass balance. Every occupant emits CO<sub>2</sub> with emission rate proportional to their breathing rate $BR_k$ and fraction of CO<sub>2</sub> in expired breath $f_{CO_2}$. Ventilation ($\lambda_{ACH}$) is the only sink of CO<sub>2</sub>, and the background concentration $C_{out}$ is set to 440 ppm. Hence,

$$
\frac{\mathrm{d}C_{CO_2}}{\mathrm{d}t}
=
\frac{(N_{inf}+N_{exp}) \cdot f_{CO_2}}{V_r}\cdot BR_k
+
\lambda_{ACH}\cdot \left(C_{out}-C_{CO_2}(t)\right).
$$

Assuming the CO<sub>2</sub> concentration is the only time-dependent variable, this equation can be solved analytically using standard techniques for ordinary differential equations (ODEs), yielding the soultion

$$
C_{CO_2}(t)
=
C_{out}
+
\frac{(N_{inf}+N_{exp}) \cdot f_{CO_2}}
     {V_r\lambda_{ACH}}\cdot BR_k
+
\left(
C_{CO_2}(t_i)
-
C_{out}
-
\frac{(N_{inf}+N_{exp}) \cdot f_{CO_2}}
     {V_r\lambda_{ACH}}\cdot BR_k
\right)
\exp(-\lambda_{ACH}(t-t_i)).
$$

$C_{CO_2}(t)$ is calculated stepwise over time intervals $[t_i, t_{i+1}]$ where the assumption that the CO<sub>2</sub> concentration is the only time-dependent variable holds. $C_{CO_2,t_i}$ is the CO<sub>2</sub> concentration at the end of the previous time interval.

<details>
<summary>Solving the ODE</summary>
We want to find the analytical solution of 

$$
\frac{\mathrm{d}C_{CO_2}}{\mathrm{d}t}
=
\frac{(N_{inf}+N_{exp}) \cdot f_{CO_2}}{V_r}\cdot BR_k
+
\lambda_{ACH}\cdot \left(C_{out}-C_{CO_2}(t)\right).
$$

assuming all variables except the CO<sub>2</sub> concentration are time-independent. First, observe that the homogenous solution (satisfying $\frac{\mathrm{d}C_{CO_2}}{\mathrm{d}t}+\lambda_{ACH}\cdot C_{CO_2}(t)=0$) is $C_{CO_2,h}(t)=\exp(-\lambda_{ACH}t)$, and the general solution (for constants $B_1$ and $B_2$) is hence

$$
C(t)=B_1+B_2 \cdot C_{CO_2,h}(t) = B_1+B_2 \cdot \exp(-\lambda_{ACH}t)
$$

Differentiating, we get

$$
\frac{\mathrm{d}C_{CO_2}}{\mathrm{d}t} = -B_2 \cdot \lambda_{ACH} \cdot \exp(-\lambda_{ACH}t)
$$

Combining the expressions for $\frac{\mathrm{d}C_{CO_2}}{\mathrm{d}t}$ yields

$$
B_1 = C_{out}
+
\frac{(N_{inf}+N_{exp}) \cdot f_{CO_2}}
     {V_r\lambda_{ACH}}\cdot BR_k
$$

so now we know the general solution is

$$
C(t)=C_{out}
+
\frac{(N_{inf}+N_{exp}) \cdot f_{CO_2}}
     {V_r\lambda_{ACH}}\cdot BR_k+B_2 \cdot C_{CO_2}(t).
$$

At $t=t_i$ the concentration is  
$$
C(t_i)=C_{out}
+
\frac{(N_{inf}+N_{exp}) \cdot f_{CO_2}}
     {V_r\lambda_{ACH}}\cdot BR_k+B_2 \cdot C_{CO_2}(t)
$$

so
$$
B_2 = C_{CO_2}(t_i)
-
C_{out}
-
\frac{(N_{inf}+N_{exp}) \cdot f_{CO_2}}
     {V_r\lambda_{ACH}}\cdot BR_k
$$

and so the specific solution is

$$
C_{CO_2}(t)
=
C_{out}
+
\frac{(N_{inf}+N_{exp}) \cdot f_{CO_2}}
     {V_r\lambda_{ACH}}\cdot BR_k
+
\left(
C_{CO_2}(t_i)
-
C_{out}
-
\frac{(N_{inf}+N_{exp}) \cdot f_{CO_2}}
     {V_r\lambda_{ACH}}\cdot BR_k
\right)
\exp(-\lambda_{ACH}(t-t_i)).
$$

as written above.

</details>

Note that the procedure for computing the CO<sub>2</sub> concentration follows the same structure as for computing the viral concentration (see the Physics of Viral Transmission page). Therefore, the class `models.CO2ConcentrationModel` for computing the CO<sub>2</sub> concentration inherits from `models._ConcentrationModelBase`. When computing the concentration in `models._ConcentrationModelBase`, we first normalize by the emission rate. For the CO<sub>2</sub> concentration, the emission rate is the breathing rate $BR_k$. Note that 

$$
C_{CO_2}(t)-C_{out} = BR_k \cdot f_{CO_2} \left( \frac{(N_{inf}+N_{exp})}
     {V_r\lambda_{ACH}}
+
\left(
\frac{C_{CO_2}(t_i)
-
C_{out}}{BR_k \cdot f_{CO_2}}
-
\frac{(N_{inf}+N_{exp})}
     {V_r\lambda_{ACH}}
\right)
\exp(-\lambda_{ACH}(t-t_i)) \right).
$$ 

Using induction, we can prove that $BR_k \cdot f_{CO_2}$ always is a linear factor of $C_{CO_2}(t_i)-C_{out}$ as long as $C_{CO_2}(t_0)=C_{out}$. Therefore, $BR_k \cdot f_{CO_2}$ is always a linear factor of $C_{CO_2}(t)-C_{out}$, and so we use `models._ConcentrationModelBase._normed_concentration()` to compute the normalized CO<sub>2</sub> concentration $\frac{C_{CO_2}(t_i)-C_{out}}{BR_k \cdot f_{CO_2}}$. Specifying `models.CO2ConcentrationModel.normalization_factor()` as $BR_k \cdot f_{CO_2}$ and adding the background concentration $C_{out}$ we then use `models._ConcentrationModelBase.concentration()` to compute the full CO<sub>2</sub>  concentration.

FUTURE UPDATES OF CAiMIRA
Note that the CO<sub>2</sub> concentration is a random variable since it is a function of the log-normal distributed breathing rate $BR_k$. In the current version of CAiMIRA, $BR_k$ is Monte Carlo sampled. Because $BR_k$ is a linear component of the concentration, however, it can be replaced by its expected value

$$
E[BR_k]
=
\exp\!\left(\mu_k+\frac{\sigma_k^2}{2}\right),
$$

where $\mu_k$ and $\sigma_k$ are the mean and standard deviation, respectively, of the log-normal distribution of $BR_k$. Hence, the expected CO<sub>2</sub> concentration is given by

$$
E[C_{CO_2}(t)]
=
C_{out}
+
\frac{(N_{inf}+N_{exp}) \cdot f_{CO_2}}
     {V_r\lambda_{ACH}}
\exp\!\left(\mu_k+\frac{\sigma_k^2}{2}\right)
+
\left(
C_{CO_2,0}
-
C_{out}
-
\frac{(N_{inf}+N_{exp}) \cdot f_{CO_2}}
     {V_r\lambda_{ACH}}
\exp\!\left(\mu_k+\frac{\sigma_k^2}{2}\right)
\right)
\exp(-\lambda_{ACH}t).
$$

<details>
<summary>Importance of $BR_k$ Being a Linear Component of the Concentration</summary>
Let $X$ be a random variable, $f$ be a function with input $X$, and $E$ denote the function mapping random variables to their expected value. Generally,

$f(E[X]) \neq E[f(X)]$

for example, if $f(X)=X^2$ and $X \sim \mathcal{N}(0, \sigma^2)$ then $f(E[X]) =0^2$ whereas $E[f(X)]=E[X^2]=E[X^2]-E[X]^2=Var[X]=\sigma^2$

However, if $f$ is linear, then $f(E[X]) = E[f(X)]$. In our case, $BR_k$ is indeed a linear component of the concentration.
</details>