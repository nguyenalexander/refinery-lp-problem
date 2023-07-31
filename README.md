# refinery-lp-project
Linear Optimization Model with a Simple Refinery with Buffer Tanks

This Python Pyomo optimization model is used to model a simple refinery described in the textbook 
"Optimization in Engineering Systems" by Ralph Pike.

The refinery contains an atmospheric distillation tower, reformer, catalytic cracker, and blend pools for premium 
gasoline, regular gasoline, diesel fuel, and fuel oil, with fuel gas by-products from the unit operations.

Buffer tanks are used to study different unit shutdowns.

# Mathematical Formulation
**Refinery LP Formulation**

$$ \begin{aligned}
& \max_{F} \phi = \sum_{t \ \in \ T} \bigg [
\sum_{\substack{p \\\ j}}^{P, \ TANKS_p} c_{p}F_{p,j,t} - 
c_{crude} F_{crude,crude_{source},AD,t} - 
\sum_{j}^{J} \sum_{\substack{m \\\ i}}^{M_j, \ I_j} c_{j}^{OP} F_{m,i,j,t} 
\bigg ] \\
\mbox{subject to:}
\end{aligned} $$

$$ F_{crude,crude_{source},AD,t} \leq 110,000 $$

$$ \sum_{\substack{m \\\ i}}^{M_j, \ I_j} F_{m,i,j,t} \leq CAP_{j} \quad \forall \ j \in J,\ t \in T $$

$$ F_{n,j,k,t} = \gamma_{n,j,k} \sum_{\substack{m \\\ i}}^{M_j, \ I_j} F_{m,i,j,t} \quad \forall \ j \in J,\ k \in K_j,\ t \in T $$

$$ F_{m,i,j,t} = \sum_{\substack{n \\\ k}}^{N_j, \ K_j} F_{n,j,k,t} \quad \forall \ j \in SP,\ t \in T $$

$$ F_{p,j,t} \geq DEMAND_{p,t} \quad \forall \ p \in PRODUCTS,\ j \in TANK_p,\ t \in T $$

$$ \sum_{\substack{m \\\ i}}^{M_j, \ I_j} F_{m,i,j,t} = F_{p,j,t} \quad \forall \ p \in PRODUCTS,\ j \in TANK_p,\ t \in T $$

$$ 
\sum_{\substack{m \\\ i}}^{M_j, \ I_j} \chi_{m,i,j,t}^{RON} F_{m,i,j,t} \geq \chi_{p,j,t}^{RON} F_{p,j,t} \\
\quad \forall \ p \in \\{ PG, RG \\},\ j \in \\{TANK_{PG}, TANK_{RG}\\}
$$

$$
\begin{aligned}
  &\sum_{\substack{m \\\ i}}^{M_j, \ I_j} \chi_{m,i,j,t}^{Z} F_{m,i,j,t} \leq \chi_{p,j,t}^{Z} F_{p,j,t} \\ 
  &\forall \ p \in PRODUCTS,\ j \in \\{TANK_{PG}, TANK_{RG}\\},\ z \in \\{VP_p, DEN_p, SULF_p\\}
\end{aligned}
$$

**Buffer Tank Formulation**

The following formulation describes the buffer tanks added to the refinery (for stream material $m$, tank $j$, and adjacent units $i$ and $k$ for all periods $t$):

$$
\frac{V_{m,j,t} - V_{m,j,t-1}}{\Delta t} = F_{m,i,j,t} - F_{m,j,k,t} \quad \mbox{(Inventory $V$)}
$$

$$
h_{m,j,t} = \frac{V_{m,j,t}}{A_j} \quad \mbox{(Inventory Height $h$)}
$$

$$
A_j = 2 \pi r_j h_j^{max} + \pi r_j^2 \quad \mbox{(Tank Area $A$)}
$$

$$
h_t \leq h_{max} \quad \mbox{(Maximum Inventory Height $h$)}
$$

The profit objective function must be modified to include processing costs for tank usage (e.g. heating/cooling, pressure changes, etc.), as well as material holding costs (handling) to discourage usage of the tanks in unnecessary conditions:

$$ 
\eqalign{
&\max_{F} \phi = \sum_{t \ \in \ T} \bigg [
\sum_{\substack{p \\\ j}}^{P, \ TANKS_p} c_{p}F_{p,j,t} - 
c_{crude} F_{crude,crude_{source},AD,t} - 
\sum_{j}^{J \ \in \ \\{ AD, RF, CC \\}} \ \sum_{\substack{m \\\ i}}^{M_j, \ I_j} c_{j}^{OP} F_{m,i,j,t} \\
& \qquad - \sum_{j}^{J \ \in \ TANKS} \ \sum_{\substack{m \\\ i}}^{M_j, \ I_j} c_{j}^{PROCESS} F_{m,i,j,t} -
\sum_{j}^{J \ \in \ TANKS} \ \sum_{m}^{M_j} c_{j}^{HOLD} V_{m,j,t}
\bigg ]}
$$

**Shutdown Formulation**

To indicate a unit shutdown, binary parameter $\alpha_{j,t}$ is used:

$$
\alpha_{j, t} = 
\bigg \lbrace 
\eqalign{
&1, \qquad \mbox{if unit $j$ shutdown at period $t$} \\
&0, \qquad \mbox{elsewhere}
}
$$

$\alpha_{j,t}$ can then be tied to the sum of the inlet flow rates of the corresponding unit $j$:

$$
\eqalign{
&\sum_{\substack{m \\\ i}}^{M_j, \ I_j} F_{m,i,j,t} \geq (1-\alpha_{j,t}) \ F_{j,t}^{min} \\ 
&\sum_{\substack{m \\\ i}}^{M_j, \ I_j} F_{m,i,j,t} \leq (1-\alpha_{j,t}) \ F_{j,t}^{max}
}
$$


