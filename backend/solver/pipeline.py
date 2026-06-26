# pipeline.py
# Master script: STEP → Mesh → FEA → Results
# This is the full analysis pipeline in one file

import sys
import os

# Python'a "uzaklara bakma, dosyalar tam olarak benim bulunduğum klasörde" diyoruz:
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from fea_input_writer import generate_calculix_input
from fea_runner import run_analysis, read_frd_results, print_results
def run_full_analysis(step_file, output_dir, material, loads, mesh_size=5.0):
    
    print("\n" + "★"*50)
    print("  FEA PLATFORM - FULL ANALYSIS PIPELINE")
    print("★"*50)
    
    # Step 1: Generate CalculiX input
    inp_file, n_nodes, n_elems = generate_calculix_input(
        step_file_path      = step_file,
        material            = material,
        boundary_conditions = loads,
        output_dir          = output_dir,
        mesh_size           = mesh_size
    )
    
    # Step 2: Run CalculiX
    success = run_analysis(inp_file)
    
    if not success:
        print("Pipeline failed at analysis step.")
        return None
    
    # Step 3: Read results
    frd_file = os.path.join(output_dir, "analysis.frd")
    results  = read_frd_results(frd_file)
    
    # Step 4: Print results with engineering interpretation
    print_results(results, material_yield=material['yield_strength'])
    
    return results


if __name__ == "__main__":
    
    steel = {
        "name"           : "STEEL",
        "youngs_modulus" : 210000,
        "poisson_ratio"  : 0.3,
        "density"        : 7.85e-9,
        "yield_strength" : 235
    }
    
    loads = {
        "force_z" : -10000  # 10,000 N downward
    }
    
    run_full_analysis(
        step_file  = r"C:\Users\aysal\Desktop\AI_Component_Analyzer\test_part.step",
        output_dir = r"C:\Users\aysal\Desktop\AI_Component_Analyzer",
        material   = steel,
        loads      = loads,
        mesh_size  = 5.0
    )