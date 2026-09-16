"""Legacy data-generation source extracted from the original Jupyter notebook.

Original notebook: fig3_data.ipynb
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
# |manuscripts:|P.6 - figure 3. Data generation code|
# |Code authors:|Yongjian Li$^*$ |
# |Last modify:|2021-01-12|
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

# --- code cell 4 ---
# Initial parameter values
parameter = {p: 10, c: 4, s: 3, w: 6, theta: 0.8, b: 3, B: 100, r: 0.05,
             mu: 100, sigma: 100}

# --- markdown cell 5 ---
# (see manuscript P(6) figure 3.)
#
# \begin{align}
# &F^{-1}(\alpha) \\
# &q_{t}^{d}=\frac{(\theta p-b) F^{-1}(\alpha)+B(1+r)}{w(1+r)-b} \\
# &q_{s}^{d}=F^{-1}\left(\frac{\theta p-w(1+r)}{\theta p-b}\right)
# \end{align}

# --- markdown cell 6 ---
# - Suppose X is normally distributed with $\mu=100$,$\sigma=100$
# - CDF,exp1: $F(x) = \alpha$

# --- code cell 7 ---
X = Normal(x, mu, sigma).subs(parameter)
exp1 = Eq(cdf(X)(x), alpha)
exp1

# --- markdown cell 8 ---
# - inverse exp1: $F^{-1}(\alpha) = x ,\quad \{0\leqslant \alpha \leqslant 1\}$

# --- code cell 9 ---
i_cdf = solve(exp1, x)[0]
i_cdf

# --- code cell 10 ---
# Convert a SymPy expression into a function that allows for fast numeric evaluation.
f = lambdify(alpha, i_cdf, modules=['numpy', 'sympy'])

x_0 = [i/1000 for i in range(1, 1000)]

dt = {
    "x_0": x_0,
}

df = pd.DataFrame(dt)
df['f(x)'] = df['x_0'].map(f)
df['f(x)'] = df['f(x)'].map(int)
df1 = df.drop_duplicates(subset=['f(x)']).reset_index(drop=True).copy()
df1

# --- code cell 11 ---
df1.query("`f(x)`==0")

# --- code cell 12 ---
df1.iloc[::10].to_csv("inverse(CDF)",index=None,sep='\t')

# --- markdown cell 18 ---
# $$q^d_{s}=F^{-1}\left(\frac{\theta p-w(1+r)}{\theta p-b}\right)$$

# --- code cell 19 ---
prob = (p*theta - w*(1+r))/(theta*p - b)
prob

# --- code cell 20 ---
prob =prob.subs(parameter).evalf(6)
prob

# --- code cell 21 ---
eq = Eq(cdf(X)(a), prob)
qd_s = solve(eq, a)[0].subs(parameter)
qd_s = int(qd_s)
qd_s

# --- markdown cell 26 ---
# $$q_{t}^{d}=\frac{(\theta p-b) F^{-1}(\alpha)+B(1+r)}{w(1+r)-b}$$

# --- code cell 27 ---
qd_t = ((p*theta-b) *x +B*(1+r))/(w*(1+r)-b)
qd_t

# --- code cell 28 ---
qd_t = qd_t.subs(parameter)

f2 = lambdify(x, qd_t, modules=['numpy', 'sympy'])

qd_t_values = f2(df['f(x)'])
qd_t_values = qd_t_values.to_numpy()
qd_t_values.shape

# --- code cell 29 ---
dt = {
    "x_0": x_0,
    "f(x)": qd_t_values
}
df_qd_t = pd.DataFrame(dt)
df_qd_t['f(x)'] = df_qd_t['f(x)'].map(int)
df_qd_t

# --- code cell 30 ---
df_qd_t = df_qd_t.drop_duplicates(subset=['f(x)']).reset_index(drop=True)
df_qd_t = df_qd_t.iloc[::10].reset_index(drop=True)
df_qd_t

# --- code cell 31 ---
value = solve(Eq(qd_t, qd_s), x)[0]
d1 = {
    "x_0": [cdf(X)(value).evalf()],
    "f(x)": [qd_s]
}
df_qd_t = df_qd_t.append(pd.DataFrame(d1))


value = solve(Eq(qd_t, 0), x)[0]
d1 = {
    "x_0": [cdf(X)(value).evalf()],
    "f(x)": [0]
}

df_qd_t = df_qd_t.append(pd.DataFrame(d1))
df_qd_t = df_qd_t.drop_duplicates(subset=['x_0'])
df_qd_t = df_qd_t.sort_values(by=['x_0']).reset_index(drop=True)
df_qd_t

# --- code cell 32 ---
df_qd_t_e = df_qd_t.query("@qd_s >=`f(x)` >= 0").reset_index(drop=True)
df_qd_t_e

# --- code cell 33 ---
df_qd_t.to_csv("qd_t",index=None,sep='\t')
df_qd_t_e.to_csv("qd_t_e",index=None,sep='\t')

# --- markdown cell 42 ---
# - some help fun() note here.

# --- code cell 43 ---
## note here
## Given a value, calculate the cumulative probability
value = 0
cdf(X)(value).evalf()
## Given a value, calculate the cumulative probability
value = 189.380
P(X < value).evalf(subs=parameter)
