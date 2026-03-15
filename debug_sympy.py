try:
    from sympy.logic.inference import satisfies
    print("satisfies imported")
except ImportError:
    print("satisfies NOT found")

try:
    from sympy.logic.inference import satisfiable
    print("satisfiable imported")
except ImportError:
    print("satisfiable NOT found")
