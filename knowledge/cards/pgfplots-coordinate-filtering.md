# PGFPlots coordinate filtering

Use PGFPlots coordinate filters to remove, transform, or condition coordinates only when the rule is explicit and scientifically justified. Filtering belongs in the data/plot contract, not in an opaque styling fragment.

Prefer preprocessing data when the transformation is part of the analysis. Plot-time filters are best for display-domain constraints, invalid coordinates, or well-documented view-specific transformations.

Never hide excluded observations without making the rule inspectable.

