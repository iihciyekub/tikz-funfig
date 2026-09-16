"""Legacy data-generation source extracted from the original Jupyter notebook.

Original notebook: fig6_data.ipynb
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
# |manuscripts:|P.7 - figure 6. Data generation code|
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
# #### (see manuscript P(7) figure 6.)
#
# \begin{align}
# &\theta^*=\frac{s B(1+r)(p-c-w r)+w(1+r)(p-s)\left[F^{-1}(\alpha)(w-c)-B(1+r)\right]}{p\left[F^{-1}(\alpha)(w-c)(p-s)+B(1+r)(s-c-w r)\right]}\\
# &b^*=\frac{(p-s)(w-c)w F^{-1}(\alpha)(1+r)+B s(1+r)(s-c-w r)}{F^{-1}(\alpha)(w-c)(p-s)+B(1+r)(s-c-w r)}
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
# p \cdot \theta^*=\frac{s B(1+r)(p-c-w r)+w(1+r)(p-s)\left[F^{-1}(\alpha)(w-c)-B(1+r)\right]}{p\left[F^{-1}(\alpha)(w-c)(p-s)+B(1+r)(s-c-w r)\right]} \cdot p
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
df_theta['f(x)'].max()

# --- code cell 24 ---
thetal

# --- code cell 25 ---
thetal = df_theta.query("0<=`f(x)`<=3 and index <=209").reset_index(drop=True)
thetal['f(x)'] = thetal['f(x)'] *10

thetal.to_csv("thetap_l",index=None,sep='\t')

# --- code cell 26 ---
thetar = df_theta.query("0<=`f(x)`<=1 and index >=99").reset_index(drop=True)
thetar['f(x)'] = thetar['f(x)'] *10
thetar.iloc[::10].to_csv("thetap_r",index=None,sep='\t')

# --- code cell 27 ---
thetal

# --- markdown cell 33 ---
#
# \begin{align}
# b^*=\frac{(p-s)(w-c)w F^{-1}(\alpha)(1+r)+B s(1+r)(s-c-w r)}{F^{-1}(\alpha)(w-c)(p-s)+B(1+r)(s-c-w r)}
# \end{align}

# --- code cell 34 ---
# 计算出CDF的反函数值后
fx = (p-s)*(w-c)*w *x *(1+r) +B*s*(1+r)*(s-c-w*r)
fy = ((w-c)*(p-s)*x + B*(1+r)*(s-c-w*r))
expr_b =fx/fy
expr_b

# --- code cell 35 ---
df

# --- code cell 36 ---
expr2=expr_b.subs(parameter)

b2 = lambdify(x, expr2, modules=['numpy', 'sympy'])

#df -> alpha
df_b = df.copy()

df_b['f(x)'] = df_b['f(x)'].map(b2)
df_b

# --- code cell 37 ---
df_b_l = df_b.query("0<=`f(x)`<=6.4 and index <=189").reset_index(drop=True)
df_b_l

# --- code cell 38 ---
df_b_l.to_csv("b_l",index=None,sep='\t')
df_b_l.shape

# --- code cell 39 ---
df_b_r = df_b.query("`f(x)`>=6.15 and index >=169").reset_index(drop=True)
df_b_r.to_csv("b_r",index=None,sep='\t')
df_b_r.shape

# --- code cell 40 ---
df_b_r

# --- markdown cell 49 ---
# - some help fun() note here.

# --- code cell 50 ---
## note here
## Given a value, calculate the cumulative probability
value = 0
cdf(X)(value).evalf()
## Given a value, calculate the cumulative probability
value = 189.380
P(X < value).evalf(subs=parameter)
