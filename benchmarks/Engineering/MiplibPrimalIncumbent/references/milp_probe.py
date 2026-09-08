def improve_primal(p):
    import numpy as np
    from scipy.optimize import milp, Bounds, LinearConstraint
    from scipy.sparse import csr_matrix
    a=csr_matrix((p['coefficients'],p['column_indices'],p['row_ptr']),shape=(p['n_constraints'],p['n_variables']))
    lo=[v if s in ('G','E') else -np.inf for s,v in zip(p['row_senses'],p['rhs'])]
    hi=[v if s in ('L','E') else np.inf for s,v in zip(p['row_senses'],p['rhs'])]
    result=milp(p['objective'],integrality=np.ones(p['n_variables']),bounds=Bounds(p['lower_bounds'],p['upper_bounds']),constraints=LinearConstraint(a,lo,hi),options={'time_limit':240,'threads':1})
    if result.x is None: raise ValueError('no feasible incumbent')
    return np.rint(result.x).astype(int).tolist()
