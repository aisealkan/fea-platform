# pipeline.py
# Master pipeline: STEP → Mesh → Solve → Results

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from python_solver import solve_linear_static, print_results


def run_full_analysis(step_file, output_dir, material, loads, mesh_size=8.0):

    print("\n" + "★"*50)
    print("  FEA PLATFORM - FULL ANALYSIS PIPELINE")
    print("★"*50)

    results = solve_linear_static(
        step_file_path      = step_file,
        material            = material,
        boundary_conditions = loads,
        mesh_size           = mesh_size,
    )

    if results:
        print_results(results)

    return results