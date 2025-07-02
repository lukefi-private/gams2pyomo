# --------------- THIS SCRIPT WAS AUTO-GENERATED FROM GAMS2PYOMO ---------------
# ------------------------ FILE SOURCE: 'trnsport.gms' -------------------------

using JuMP
using Ipopt


# Model name: A Transportation Problem (TRNSPORT,SEQ=1)
m = Model()

#= This problem finds a least cost shipping schedule that meets
requirements at markets and supplies at factories.


Dantzig, G B, Chapter 3.3. In Linear Programming and Extensions.
Princeton University Press, Princeton, New Jersey, 1963.

This formulation is described in detail in:
Rosenthal, R E, Chapter 2: A GAMS Tutorial. In GAMS: A User's Guide.
The Scientific Press, Redwood City, California, 1988.

The line numbers will not match those in the book because of these
comments.

Keywords: linear programming, transportation problem, scheduling
 =#

m_I = ["seattle", "san_diego"] # canning plants
m_J = ["new_york", "chicago", "topeka"] # markets
m_a = Dict([('seattle', 350), ('san_diego', 600)])
m_b = Dict([('new_york', 325), ('chicago', 300), ('topeka', 275)])
m_d = Dict({('seattle', 'new_york'): 2.5, ('seattle', 'chicago'): 1.7, ('seattle', 'topeka'): 1.8, ('san_diego', 'new_york'): 2.5, ('san_diego', 'chicago'): 1.8, ('san_diego', 'topeka'): 1.4})
f = 90 # freight in dollars per case per thousand miles 
[i in I][i in J]) # transport cost in thousands of dollars per case
c = (f * d) / 1000
@variable(m, x, m_I, m_J) # shipment quantities in cases
@variable(m, z, ) # total transportation costs in thousands of dollars
set_lower_bound(x, 0.0)
@constraint(m, cost, z == sum((c * x) for i in m_I for j in m_J))
@constraint(m, supply, , isum(x for j in m_J) <= a)
@constraint(m, demand, , jsum(x for i in m_I) >= b)
m_transport = copy(m)
@objective(m_transport, Min, m_transport[:z])
set_optimizer(m_transport, () -> Ipopt.Optimizer())
optimize!(m_transport)
print(value(m_x))
