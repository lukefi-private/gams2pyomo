# --------------- THIS SCRIPT WAS AUTO-GENERATED FROM GAMS2PYOMO ---------------
# ------------------------ FILE SOURCE: 'trnsport.gms' -------------------------

from pyomo.environ import *


m = ConcreteModel(name='A Transportation Problem (TRNSPORT,SEQ=1)')

"""This problem finds a least cost shipping schedule that meets
requirements at markets and supplies at factories.


Dantzig, G B, Chapter 3.3. In Linear Programming and Extensions.
Princeton University Press, Princeton, New Jersey, 1963.

This formulation is described in detail in:
Rosenthal, R E, Chapter 2: A GAMS Tutorial. In GAMS: A User's Guide.
The Scientific Press, Redwood City, California, 1988.

The line numbers will not match those in the book because of these
comments.

Keywords: linear programming, transportation problem, scheduling
"""

m.I = Set(initialize=['seattle', 'san_diego'], ordered=True, doc='canning plants')
m.J = Set(initialize=['new_york', 'chicago', 'topeka'], ordered=True, doc='markets')
m.a = Param(m.I, mutable=True, initialize={'seattle': 350, 'san_diego': 600}, doc='capacity of plant i in cases')
m.b = Param(m.J, mutable=True, initialize={'new_york': 325, 'chicago': 300, 'topeka': 275}, doc='demand at market j in cases')
m.d = Param(m.I, m.J, mutable=True, initialize={('seattle', 'new_york'): 2.5, ('seattle', 'chicago'): 1.7, ('seattle', 'topeka'): 1.8, ('san_diego', 'new_york'): 2.5, ('san_diego', 'chicago'): 1.8, ('san_diego', 'topeka'): 1.4}, doc='distance in thousands of miles')
m.f = Param(mutable=True, initialize=90, doc='freight in dollars per case per thousand miles')
m.c = Param(m.I, m.J, mutable=True, doc='transport cost in thousands of dollars per case')
for i in m.I:
	for j in m.J:
		m.c[i, j] = (m.f * m.d[i, j]) / 1000
m.x = Var(m.I, m.J, doc='shipment quantities in cases')
m.z = Var(doc='total transportation costs in thousands of dollars')
m.x.domain = NonNegativeReals
def cost(m):
	return m.z == sum((m.c[i, j] * m.x[i, j]) for i in m.I for j in m.J)
m.cost = Constraint(rule=cost)
def supply(m, i):
	return sum(m.x[i, j] for j in m.J) <= m.a[i]
m.supply = Constraint(m.I, rule=supply)
def demand(m, j):
	return sum(m.x[i, j] for i in m.I) >= m.b[j]
m.demand = Constraint(m.J, rule=demand)
m_transport = m.clone()
m_transport._obj_ = Objective(rule=m_transport.z, sense=1)
opt = SolverFactory('gurobi')
opt.solve(m_transport, tee=True)
m.x.pprint()
