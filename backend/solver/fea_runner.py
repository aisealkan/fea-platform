# fea_runner.py
# Runs CalculiX and reads the results
#
# CalculiX produces two result files:
#   analysis.frd  = contains displacements and stresses for all nodes
#   analysis.dat  = contains summary statistics

import subprocess
import os
import re

# Path to CalculiX executable
CALCULIX_PATH = r"C:\CalculiX\ccx.exe"

def run_analysis(inp_file_path):
    """
    Runs CalculiX on the input file.
    
    CalculiX is called from command line like:
        ccx.exe -i analysis
    (note: no .inp extension, CalculiX adds it automatically)
    """
    
    print("\n" + "="*50)
    print("  RUNNING FEA ANALYSIS")
    print("="*50)
    
    if not os.path.exists(inp_file_path):
        print(f"ERROR: Input file not found: {inp_file_path}")
        return False
    
    if not os.path.exists(CALCULIX_PATH):
        print(f"ERROR: CalculiX not found at: {CALCULIX_PATH}")
        return False
    
    # Job name = filename without extension
    job_name    = os.path.splitext(inp_file_path)[0]
    working_dir = os.path.dirname(inp_file_path)
    
    print(f"Input file : {inp_file_path}")
    print(f"Job name   : {job_name}")
    print(f"Running CalculiX...")
    
    # Run CalculiX as a subprocess
    # subprocess = running another program from within Python
    result = subprocess.run(
        [CALCULIX_PATH, "-i", job_name],
        cwd     = working_dir,
        capture_output = True,
        text    = True
    )
    
    # Check if it succeeded
    if result.returncode != 0:
        print("ERROR: CalculiX failed.")
        print(result.stderr)
        return False
    
    print("✓ CalculiX completed successfully.")
    return True


def read_frd_results(frd_file_path):
    """
    Reads the .frd result file from CalculiX.
    
    .frd file contains:
    - Node displacements (U1, U2, U3 = movement in X, Y, Z)
    - Stresses at each node (S11, S22, S33, S12, S13, S23)
    
    We extract:
    - Maximum displacement
    - Von Mises stress at each node
    - Maximum Von Mises stress and where it occurs
    """
    
    print("\n[Reading results...]")
    
    if not os.path.exists(frd_file_path):
        print(f"ERROR: Result file not found: {frd_file_path}")
        return None
    
    displacements = {}  # node_id → (ux, uy, uz)
    stresses      = {}  # node_id → (s11, s22, s33, s12, s13, s23)
    
    current_block = None
    
    with open(frd_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Detect displacement block
            if 'DISP' in line or 'U1' in line:
                current_block = 'displacement'
                continue
            
            # Detect stress block
            if 'STRESS' in line or 'SXX' in line:
                current_block = 'stress'
                continue
            
            # Parse displacement values
            if current_block == 'displacement' and line.startswith('-1'):
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        node = int(parts[1])
                        ux   = float(parts[2])
                        uy   = float(parts[3])
                        uz   = float(parts[4])
                        displacements[node] = (ux, uy, uz)
                    except:
                        pass
            
            # Parse stress values
            if current_block == 'stress' and line.startswith('-1'):
                parts = line.split()
                if len(parts) >= 7:
                    try:
                        node = int(parts[1])
                        s11  = float(parts[2])
                        s22  = float(parts[3])
                        s33  = float(parts[4])
                        s12  = float(parts[5])
                        s13  = float(parts[6])
                        s23  = float(parts[7]) if len(parts) > 7 else 0.0
                        stresses[node] = (s11, s22, s33, s12, s13, s23)
                    except:
                        pass
    
    # Calculate Von Mises stress for each node
    # Von Mises = combined stress measure used to predict yielding
    # Formula: sqrt(0.5 * ((s11-s22)² + (s22-s33)² + (s33-s11)² + 6*(s12²+s23²+s13²)))
    von_mises = {}
    for node, (s11, s22, s33, s12, s13, s23) in stresses.items():
        vm = (0.5 * (
            (s11-s22)**2 +
            (s22-s33)**2 +
            (s33-s11)**2 +
            6 * (s12**2 + s23**2 + s13**2)
        )) ** 0.5
        von_mises[node] = vm
    
    # Find maximum values
    if displacements:
        total_disp = {
            n: (ux**2 + uy**2 + uz**2)**0.5
            for n, (ux, uy, uz) in displacements.items()
        }
        max_disp_node  = max(total_disp, key=total_disp.get)
        max_disp_value = total_disp[max_disp_node]
    else:
        max_disp_node  = None
        max_disp_value = 0
    
    if von_mises:
        max_vm_node  = max(von_mises, key=von_mises.get)
        max_vm_value = von_mises[max_vm_node]
    else:
        max_vm_node  = None
        max_vm_value = 0
    
    return {
        "displacements"     : displacements,
        "von_mises"         : von_mises,
        "max_displacement"  : max_disp_value,
        "max_disp_node"     : max_disp_node,
        "max_von_mises"     : max_vm_value,
        "max_vm_node"       : max_vm_node,
        "num_nodes_parsed"  : len(displacements)
    }


def print_results(results, material_yield=235.0):
    """
    Prints analysis results with engineering interpretation.
    
    Safety factor = yield strength / max Von Mises stress
    If safety factor < 1.0 → part will yield (fail)
    If safety factor > 1.0 → part is safe
    Typical engineering requirement: safety factor > 2.0
    """
    
    if results is None:
        print("No results to display.")
        return
    
    max_vm   = results['max_von_mises']
    max_disp = results['max_displacement']
    
    # Safety factor calculation
    if max_vm > 0:
        safety_factor = material_yield / max_vm
    else:
        safety_factor = 999
    
    # Engineering assessment
    if safety_factor >= 2.0:
        assessment = "SAFE - Meets typical engineering standards (SF ≥ 2.0)"
    elif safety_factor >= 1.5:
        assessment = "MARGINAL - Acceptable for some applications (SF ≥ 1.5)"
    elif safety_factor >= 1.0:
        assessment = "WARNING - Part will not yield but margin is very low"
    else:
        assessment = "CRITICAL - Part will yield under this load!"
    
    print("\n" + "="*50)
    print("  ANALYSIS RESULTS")
    print("="*50)
    print(f"  Nodes analyzed     : {results['num_nodes_parsed']:,}")
    print(f"  Max displacement   : {max_disp:.4f} mm")
    print(f"  Max Von Mises      : {max_vm:.2f} MPa")
    print(f"  Yield strength     : {material_yield:.2f} MPa")
    print(f"  Safety factor      : {safety_factor:.2f}")
    print("-"*50)
    print(f"  Assessment: {assessment}")
    print("="*50)


if __name__ == "__main__":
    
    base_dir = r"C:\Users\aysal\Desktop\AI_Component_Analyzer"
    inp_file = os.path.join(base_dir, "analysis.inp")
    frd_file = os.path.join(base_dir, "analysis.frd")
    
    # Run CalculiX
    success = run_analysis(inp_file)
    
    if success:
        # Read results
        results = read_frd_results(frd_file)
        print_results(results, material_yield=235.0)
    else:
        print("\nAnalysis failed. Check the input file.")