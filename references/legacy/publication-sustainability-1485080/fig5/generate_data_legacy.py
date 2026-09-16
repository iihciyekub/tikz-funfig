"""Legacy data-generation source extracted from the original Jupyter notebook.

Original notebook: fig5_data.ipynb
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
# |manuscripts:|P.7 - figure 5. Data generation code|
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

# --- markdown cell 6 ---
# #### (see manuscript P(7) figure 5.)
#
# \begin{align}
# \theta^*=\frac{s B(1+r)(p-c-w r)+w(1+r)(p-s)\left[F^{-1}(\alpha)(w-c)-B(1+r)\right]}{p\left[F^{-1}(\alpha)(w-c)(p-s)+B(1+r)(s-c-w r)\right]}
# \end{align}

# --- markdown cell 7 ---
# - Suppose X is normally distributed with $\mu=100$,$\sigma=100$
# - CDF,exp1: $F(x) = \alpha$

# --- code cell 8 ---
X = Normal(x, mu, sigma).subs(parameter)
exp1 = Eq(cdf(X)(x), alpha)
exp1

# --- markdown cell 9 ---
# - inverse exp1: $F^{-1}(\alpha) = x ,\quad \{0\leqslant \alpha \leqslant 1\}$

# --- code cell 10 ---
i_cdf = solve(exp1, x)[0]
i_cdf

# --- code cell 11 ---
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

# --- code cell 12 ---
df1.query("`f(x)`==0")

# --- code cell 13 ---
# df1.iloc[::10].to_csv("inverse(CDF)",index=None,sep='\t')

# --- markdown cell 19 ---
# \begin{align}
# \theta^*=\frac{s B(1+r)(p-c-w r)+w(1+r)(p-s)\left[F^{-1}(\alpha)(w-c)-B(1+r)\right]}{p\left[F^{-1}(\alpha)(w-c)(p-s)+B(1+r)(s-c-w r)\right]}
# \end{align}

# --- code cell 20 ---
fa = s*B*(1+r)*(p-c-w*r)+w*(1+r)*(p-s)*(x *(w-c)-B*(1+r))
fb = ((w-c)*(p-s)*x + B*(1+r)*(s-c-w*r))
expr =fa/(fb*p)
expr

# --- code cell 21 ---
df

# --- code cell 22 ---
expr1=expr.subs(parameter)

f2 = lambdify(x, expr1, modules=['numpy', 'sympy'])

#df -> alpha
df_theta = df.copy()

df_theta['f(x)'] = df_theta['f(x)'].map(f2)
df_theta

# --- code cell 23 ---
thetal = df_theta.query("0<=`f(x)`<=1 and index <=99").reset_index(drop=True)
thetal.to_csv("thetal",index=None,sep='\t')

# --- code cell 24 ---
thetar = df_theta.query("0<=`f(x)`<=1 and index >=99").reset_index(drop=True)
thetar.iloc[::10].to_csv("thetar",index=None,sep='\t')

# --- code cell 25 ---
thetal

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
