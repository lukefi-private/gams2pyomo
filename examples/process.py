# --------------- THIS SCRIPT WAS AUTO-GENERATED FROM GAMS2PYOMO ---------------
# ------------------------- FILE SOURCE: 'process.gms' -------------------------

from pyomo.environ import *


m = ConcreteModel(name='Alkylation Process Optimization (PROCESS,SEQ=20)')

"""Optimization of a alkylation process.


Bracken, J, and McCormick, G P, Chapter 4. In Selected Applications
of Nonlinear Programming. John Wiley and Sons, New York, 1968.

Keywords: nonlinear programming, alkylation process, chemical engineering
"""

m.olefin = Var(within=NonNegativeReals, doc='olefin feed                   (bpd)')
m.isor = Var(within=NonNegativeReals, doc='isobutane recycle             (bpd)')
m.acid = Var(within=NonNegativeReals, doc='acid addition rate (1000lb per day)')
m.alkylate = Var(within=NonNegativeReals, doc='alkylate yield                (bpd)')
m.isom = Var(within=NonNegativeReals, doc='isobutane makeup              (bpd)')
m.strength = Var(within=NonNegativeReals, doc='acid strength          (weight pct)')
m.octane = Var(within=NonNegativeReals, doc='motor octane number')
m.ratio = Var(within=NonNegativeReals, doc='isobutane makeup to olefin ratio')
m.dilute = Var(within=NonNegativeReals, doc='acid dilution factor')
m.f4 = Var(within=NonNegativeReals, doc='f-4 performance number')
m.profit = Var()
m.rangey = Var()
m.rangem = Var()
m.ranged = Var()
m.rangef = Var()
def yield_(m):
	return m.alkylate == (m.olefin * (1.12 + 0.13167 * m.ratio - 0.00667 * (m.ratio) ** 2))
m.yield_ = Constraint(rule=yield_)
def makeup(m):
	return m.alkylate == (m.olefin + m.isom - 0.22 * m.alkylate)
m.makeup = Constraint(rule=makeup)
def sdef(m):
	return m.acid == ((((m.alkylate * m.dilute) * m.strength) / (98 - m.strength)) / 1000)
m.sdef = Constraint(rule=sdef)
def motor(m):
	return m.octane == (86.35 + 1.098 * m.ratio - 0.038 * (m.ratio) ** 2 - 0.325 * (89 - m.strength))
m.motor = Constraint(rule=motor)
def drat(m):
	return m.ratio == ((m.isor + m.isom) / m.olefin)
m.drat = Constraint(rule=drat)
def ddil(m):
	return m.dilute == (35.82 - 0.222 * m.f4)
m.ddil = Constraint(rule=ddil)
def df4(m):
	return m.f4 == (-133 + 3 * m.octane)
m.df4 = Constraint(rule=df4)
def dprofit(m):
	return m.profit == ((0.063 * m.alkylate) * m.octane - 5.04 * m.olefin - 0.035 * m.isor - 10 * m.acid - 3.36 * m.isom)
m.dprofit = Constraint(rule=dprofit)
def rngyield(m):
	return (m.rangey * m.alkylate) == (m.olefin * (1.12 + 0.13167 * m.ratio - 0.00667 * (m.ratio) ** 2))
m.rngyield = Constraint(rule=rngyield)
def rngmotor(m):
	return (m.rangem * m.octane) == (86.35 + 1.098 * m.ratio - 0.038 * (m.ratio) ** 2 - 0.325 * (89 - m.strength))
m.rngmotor = Constraint(rule=rngmotor)
def rngddil(m):
	return (m.ranged * m.dilute) == (35.82 - 0.222 * m.f4)
m.rngddil = Constraint(rule=rngddil)
def rngdf4(m):
	return (m.rangef * m.f4) == (-133 + 3 * m.octane)
m.rngdf4 = Constraint(rule=rngdf4)
m.rangey.setlb(0.9)
m.rangey.setub(1.1)
m.rangey = 1
m.rangem.setlb(0.9)
m.rangem.setub(1.1)
m.rangem = 1
m.ranged.setlb(0.9)
m.ranged.setub(1.1)
m.ranged = 1
m.rangef.setlb(0.9)
m.rangef.setub(1.1)
m.rangef = 1
m.strength.setlb(85)
m.strength.setub(93)
m.octane.setlb(90)
m.octane.setub(95)
m.ratio.setlb(3)
m.ratio.setub(12)
m.dilute.setlb(1.2)
m.dilute.setub(4)
m.f4.setlb(145)
m.f4.setub(162)
m.olefin.setlb(10)
m.olefin.setub(2000)
m.isor.setub(16000)
m.acid.setub(120)
m.alkylate.setub(5000)
m.isom.setub(2000)
m.olefin = 1745
m.isor = 12000
m.acid = 110
m.alkylate = 3048
m.isom = 1974
m.strength = 89.2
m.octane = 92.8
m.ratio = 8
m.dilute = 3.6
m.f4 = 145
m.profit = 872
m_process = m.clone()
m_process.del_component('rngyield')
m_process.del_component('rngmotor')
m_process.del_component('rngddil')
m_process.del_component('rngdf4')
m_process._obj_ = Objective(rule=m_process.profit, sense=-1)
opt = SolverFactory('ipopt')
opt.solve(m_process, tee=True)
m_rproc = m.clone()
m_rproc.del_component('yield_')
m_rproc.del_component('motor')
m_rproc.del_component('ddil')
m_rproc.del_component('df4')
m_rproc._obj_ = Objective(rule=m_rproc.profit, sense=-1)
opt = SolverFactory('ipopt')
opt.solve(m_rproc, tee=True)
