"""Legacy data-generation source extracted from the original Jupyter notebook.

Original notebook: fig2_data.ipynb
This file preserves historical computation cells for provenance and review.
It is not modernized and may require the original package versions to execute.
Notebook-only or syntactically incomplete cells are preserved as comments.
"""

# --- markdown cell 1 ---
# |      |      |
# | ---- | ---- |
# | Journal:|Sustainability (ISSN 2071-1050)|
# |Manuscript ID:| sustainability-1485080|
# |Type:|Article|
# |Title:|NEVs Supply Chain Coordination with Financial Constraint and Demand Uncertainty|
# |manuscripts:|P.5 - figure 2. Data generation code|
# |Code authors:|Yongjian Li$^*$ |
# |Last modify:|2021-01-11|
# |version:|Python 3.6.5, sympy >= 1.3|

# --- code cell 2 ---
from sympy import *
from sympy.stats import *
import numpy as np
import pandas as pd
# init_printing(use_unicode=True)
import sympy
sympy.__version__

# --- code cell 3 ---
p, w, c, s, B, b, r, alpha, theta, q, a, x, r, mu, sigma, y = symbols(
    "p,w,c,s,B,b,r,alpha,theta,q,a,x,r,mu,sigma,y")

# --- markdown cell 4 ---
# >  Suppose $x$ is a Normal distribution with parameters $\mu = 100, \sigma = 100$

# --- code cell 5 ---
# Initial parameter values
parameter = {p: 10, c: 4, s: 3, w: 6, B: 100, r: 0.05,
             mu: 100, sigma: 100}

# --- code cell 6 ---
X = Normal(x, mu, sigma).subs(parameter)

# --- markdown cell 7 ---
# (see manuscript P(5) figure 1.)
# \begin{align}
# &F^{-1}(\alpha) \\
# &q_{t}=\frac{(p-s) F^{-1}(\alpha)+B(1+r)}{w(1+r)-s} \\
# &q_{s}=F^{-1}\left(\frac{p-c-w r}{p-s}\right)
# \end{align}

# --- markdown cell 8 ---
# - exp1: $F(x) = \alpha$

# --- code cell 9 ---
exp1 = Eq(cdf(X)(x), alpha)
exp1

# --- markdown cell 10 ---
# - inverse exp1: $F^{-1}(\alpha) = x ,\quad \{0\leqslant \alpha \leqslant 1\}$

# --- code cell 11 ---
i_cdf = solve(exp1, x)[0]
i_cdf

# --- code cell 12 ---
# Convert a SymPy expression into a function that allows for fast numeric evaluation.
f = lambdify(alpha, i_cdf, modules=['numpy', 'sympy'])

x = [i/1000 for i in range(1, 1000)]

dt = {
    "x_0": x,
}

df = pd.DataFrame(dt)
df['f(x)'] = df['x_0'].map(f)
df['f(x)'] = df['f(x)'].map(int)
df1 = df.drop_duplicates(subset=['f(x)']).reset_index(drop=True)
df1

# --- code cell 13 ---
df1.query("`f(x)`==0")

# --- code cell 14 ---
# df1.to_csv("inverse(CDF)",index=None,sep='\t')

# --- markdown cell 18 ---
# $$q_{t}=\frac{(p-s) F^{-1}(\alpha)+B(1+r)}{w(1+r)-s} $$

# --- code cell 19 ---

qt_f = ((p-s) * a + B*(1+r))/(w*(1+r)-s)
qt_f = qt_f.subs(parameter)

f2 = lambdify(a, qt_f, modules=['numpy', 'sympy'])

qt_values = f2(df['f(x)'])
qt_values = qt_values.to_numpy()

# --- code cell 20 ---

dt = {
    "x_0": x,
    "f(x)": qt_values
}
df_qt = pd.DataFrame(dt)
df_qt['f(x)'] = df_qt['f(x)'].map(int)
df_qt = df_qt.drop_duplicates(subset=['f(x)']).reset_index(drop=True)
df_qt = df_qt.iloc[::10].reset_index(drop=True)
df_qt

# --- markdown cell 21 ---
# $$q_{s}=F^{-1}\left(\frac{p-c-w r}{p-s}\right)$$

# --- code cell 22 ---
alpha_value = (p-c - w*r)/(p - s)
alpha_value = alpha_value.subs(parameter)
alpha_value

# --- code cell 23 ---
# Calculate  qs
qs = int(f(alpha_value))
qs

# --- code cell 24 ---
# add point (0,189)
value = solve(Eq(qt_f, qs), a)[0]
d1 = {
    "x_0": [cdf(X)(value).evalf()],
    "f(x)": [qs]
}
df_qt = df_qt.append(pd.DataFrame(d1))


value = solve(Eq(qt_f, 0), a)[0]
d1 = {
    "x_0": [cdf(X)(value).evalf()],
    "f(x)": [0]
}

df_qt = df_qt.append(pd.DataFrame(d1))
df_qt = df_qt.drop_duplicates(subset=['x_0'])
df_qt = df_qt.sort_values(by=['x_0']).reset_index(drop=True)
df_qt

# --- code cell 25 ---
df_qt1 = df_qt.query("@qs >=`f(x)` >= 0").reset_index(drop=True)
df_qt1

# --- markdown cell 26 ---
# # 计算 利润
# $\pi^\star(q^c) = q(p-c)-(p-s) \int_{0}^{q} F(x) d x-(w q-B)^{+} r$

# --- code cell 27 ---
p, w, c, s, B, b, r, alpha, theta, q, a, x, r, mu, sigma, y = symbols(
    "p,w,c,s,B,b,r,alpha,theta,q,a,x,r,mu,sigma,y")

# --- code cell 28 ---
pi_qc = q*(p-c) - (p-s)*integrate(cdf(X)(x), (x, 0, q)) - Max(0,w*q-B)*r
pi_qc = pi_qc.subs(parameter)
pi_qc

# --- code cell 29 ---
pi_f = lambdify(q,pi_qc, modules=['numpy', 'sympy'])

# --- code cell 30 ---
df_qt['f(x)'] = df_qt['f(x)'].map(pi_f)
df_qt

# --- code cell 31 ---
df_qt.to_csv("piqc",index=None,sep='\t')

# --- code cell 32 ---
df_qt.query("0.40>=`x_0`>=0.12").to_csv("piqc_in",index=None,sep='\t')

# --- markdown cell 38 ---
# - some help fun() note here.

# --- code cell 39 ---
## note here
## Given a value, calculate the cumulative probability
value = 0
cdf(X)(value).evalf()
## Given a value, calculate the cumulative probability
value = 189.380
P(X < value).evalf(subs=parameter)
