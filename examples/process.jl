# --------------- THIS SCRIPT WAS AUTO-GENERATED FROM GAMS2PYOMO ---------------
# ------------------------- FILE SOURCE: 'process.gms' -------------------------

using JuMP
using Ipopt


# Model name: Alkylation Process Optimization (PROCESS,SEQ=20)
m = Model()

#= Optimization of a alkylation process.


Bracken, J, and McCormick, G P, Chapter 4. In Selected Applications
of Nonlinear Programming. John Wiley and Sons, New York, 1968.

Keywords: nonlinear programming, alkylation process, chemical engineering
 =#

@variable(m, olefin, lower_bound = 0) # olefin feed                   (bpd)
@variable(m, isor, lower_bound = 0) # isobutane recycle             (bpd)
@variable(m, acid, lower_bound = 0) # acid addition rate (1000lb per day)
@variable(m, alkylate, lower_bound = 0) # alkylate yield                (bpd)
@variable(m, isom, lower_bound = 0) # isobutane makeup              (bpd)
@variable(m, strength, lower_bound = 0) # acid strength          (weight pct)
@variable(m, octane, lower_bound = 0) # motor octane number
@variable(m, ratio, lower_bound = 0) # isobutane makeup to olefin ratio
@variable(m, dilute, lower_bound = 0) # acid dilution factor
@variable(m, f4, lower_bound = 0) # f-4 performance number
@variable(m, profit, )
@variable(m, rangey, )
@variable(m, rangem, )
@variable(m, ranged, )
@variable(m, rangef, )
@constraint(m, yield_, alkylate == (olefin * (1.12 + 0.13167 * ratio - 0.00667 * (ratio) ^ 2)))
@constraint(m, makeup, alkylate == (olefin + isom - 0.22 * alkylate))
@constraint(m, sdef, acid == ((((alkylate * dilute) * strength) / (98 - strength)) / 1000))
@constraint(m, motor, octane == (86.35 + 1.098 * ratio - 0.038 * (ratio) ^ 2 - 0.325 * (89 - strength)))
@constraint(m, drat, ratio == ((isor + isom) / olefin))
@constraint(m, ddil, dilute == (35.82 - 0.222 * f4))
@constraint(m, df4, f4 == (-133 + 3 * octane))
@constraint(m, dprofit, profit == ((0.063 * alkylate) * octane - 5.04 * olefin - 0.035 * isor - 10 * acid - 3.36 * isom))
@constraint(m, rngyield, (rangey * alkylate) == (olefin * (1.12 + 0.13167 * ratio - 0.00667 * (ratio) ^ 2)))
@constraint(m, rngmotor, (rangem * octane) == (86.35 + 1.098 * ratio - 0.038 * (ratio) ^ 2 - 0.325 * (89 - strength)))
@constraint(m, rngddil, (ranged * dilute) == (35.82 - 0.222 * f4))
@constraint(m, rngdf4, (rangef * f4) == (-133 + 3 * octane))
set_lower_bound(rangey, 0.9)
set_upper_bound(rangey, 1.1)
set_start_value(rangey, 1)
set_lower_bound(rangem, 0.9)
set_upper_bound(rangem, 1.1)
set_start_value(rangem, 1)
set_lower_bound(ranged, 0.9)
set_upper_bound(ranged, 1.1)
set_start_value(ranged, 1)
set_lower_bound(rangef, 0.9)
set_upper_bound(rangef, 1.1)
set_start_value(rangef, 1)
set_lower_bound(strength, 85)
set_upper_bound(strength, 93)
set_lower_bound(octane, 90)
set_upper_bound(octane, 95)
set_lower_bound(ratio, 3)
set_upper_bound(ratio, 12)
set_lower_bound(dilute, 1.2)
set_upper_bound(dilute, 4)
set_lower_bound(f4, 145)
set_upper_bound(f4, 162)
set_lower_bound(olefin, 10)
set_upper_bound(olefin, 2000)
set_upper_bound(isor, 16000)
set_upper_bound(acid, 120)
set_upper_bound(alkylate, 5000)
set_upper_bound(isom, 2000)
set_start_value(olefin, 1745)
set_start_value(isor, 12000)
set_start_value(acid, 110)
set_start_value(alkylate, 3048)
set_start_value(isom, 1974)
set_start_value(strength, 89.2)
set_start_value(octane, 92.8)
set_start_value(ratio, 8)
set_start_value(dilute, 3.6)
set_start_value(f4, 145)
set_start_value(profit, 872)
m_process = copy(m)
delete(m_process, m_process[:rngyield])
unregister(m_process, :rngyield)
delete(m_process, m_process[:rngmotor])
unregister(m_process, :rngmotor)
delete(m_process, m_process[:rngddil])
unregister(m_process, :rngddil)
delete(m_process, m_process[:rngdf4])
unregister(m_process, :rngdf4)
@objective(m_process, Max, m_process[:profit])
set_optimizer(m_process, () -> Ipopt.Optimizer())
optimize!(m_process)
m_rproc = copy(m)
delete(m_rproc, m_rproc[:yield_])
unregister(m_rproc, :yield_)
delete(m_rproc, m_rproc[:motor])
unregister(m_rproc, :motor)
delete(m_rproc, m_rproc[:ddil])
unregister(m_rproc, :ddil)
delete(m_rproc, m_rproc[:df4])
unregister(m_rproc, :df4)
@objective(m_rproc, Max, m_rproc[:profit])
set_optimizer(m_rproc, () -> Ipopt.Optimizer())
optimize!(m_rproc)
