"""Legacy data-generation source extracted from the original Jupyter notebook.

Original notebook: fig9_data.ipynb
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
# |manuscripts:|P.9 - figure 9. Data generation code|
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
# #### (see manuscript P(9) figure 9.)
#
#
# \begin{align}
# &F^{-1}(\alpha) \\
# &\bar{B}=(c(1+r)-s) F^{-1}\left(\frac{p-c(1+r)}{p-s}\right)-(p-s) F^{-1}(\alpha)
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
df1 = df.copy()
df1['f(x)'] = df1['f(x)'].map(int)
df1 = df1.drop_duplicates(subset=['f(x)']).reset_index(drop=True).copy()
df1

# --- code cell 11 ---
df1.query("`f(x)`==0")

# --- code cell 12 ---
# df1.iloc[::10].to_csv("inverse(CDF)",index=None,sep='\t')

# --- markdown cell 16 ---
# $$\bar{B}=(c(1+r)-s) F^{-1}\left(\frac{p-c(1+r)}{p-s}\right)-(p-s) F^{-1}(\alpha)$$

# --- code cell 17 ---
prob = (p-c *(1+r))/(p - s)
prob

# --- code cell 18 ---
prob = prob.subs(parameter)
eq = Eq(cdf(X)(x), prob)
qs = solve(eq, x)[0].evalf(subs=parameter)
qs =int(qs)
qs

# --- code cell 19 ---
expr1 = (c*(1+r)-s)*194.853504082664 - (p-s) * x
expr1

# --- code cell 20 ---
f2 = lambdify(x, expr1.subs(parameter), modules=['numpy', 'sympy'])

piqc = df.copy()
piqc['f(x)'] = piqc['f(x)'].map(float)
piqc['f(x)'] = piqc['f(x)'].map(f2)
piqc

# --- code cell 21 ---
piqc.query("x_0 == 0.252")

# --- code cell 22 ---
piqc.iloc[::5].to_csv("Bbar",index=None,sep='\t')

# --- markdown cell 34 ---
# - some help fun() note here.

# --- code cell 35 ---
## note here
## Given a value, calculate the cumulative probability
value = 0
cdf(X)(value).evalf()
## Given a value, calculate the cumulative probability
value = 189.380
P(X < value).evalf(subs=parameter)
