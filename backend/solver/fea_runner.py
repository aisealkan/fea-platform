# fea_runner.py
import subprocess
import os

CALCULIX_PATH = r"C:\Users\aysal\Downloads\CalculiX-2.20.0-win-x64\CalculiX-2.20.0-win-x64\bin\ccx.exe"


def run_analysis(inp_file_path):

    print("\n" + "="*50)
    print("  RUNNING FEA ANALYSIS")
    print("="*50)

    if not os.path.exists(inp_file_path):
        print(f"ERROR: Input file not found: {inp_file_path}")
        return False

    if not os.path.exists(CALCULIX_PATH):
        print(f"ERROR: CalculiX not found at: {CALCULIX_PATH}")
        return False

    working_dir = os.path.dirname(inp_file_path)
    print(f"Input file : {inp_file_path}")
    print(f"Running CalculiX...")

    result = subprocess.run(
        [CALCULIX_PATH, "-i", "analysis"],
        cwd=working_dir,
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode != 0:
        print("ERROR: CalculiX failed with return code:", result.returncode)
        return False

    frd_path = os.path.join(working_dir, "analysis.frd")
    if not os.path.exists(frd_path):
        print("ERROR: analysis.frd oluşmadı!")
        return False

    print("✓ CalculiX completed successfully.")
    return True


def read_frd_results(frd_file_path):
    """
    .frd dosyası formatı (null-byte temizlendikten sonra):

    Satır formatı:
      ' -1         1-5.00000E+001-2.50000E+001-1.25000E+001'
       [0:3]  = ' -1'          → veri satırı işareti
       [3:13] = '         1'   → node ID (10 karakter, sağa hizalı)
       [13:26]= '-5.00000E+001' → değer 1 (13 karakter)
       [26:39]= '-2.50000E+001' → değer 2 (13 karakter)
       [39:52]= '-1.25000E+001' → değer 3 (13 karakter)
       [52:65]= ...             → değer 4 (stress için)
       [65:78]= ...             → değer 5 (stress için)
       [78:91]= ...             → değer 6 (stress için)
    """

    print("\n[Reading results...]")

    if not os.path.exists(frd_file_path):
        print(f"ERROR: Result file not found: {frd_file_path}")
        return None

    # UTF-16 LE ile yazılmış, null byte'ları temizle
    with open(frd_file_path, 'rb') as fb:
        content = fb.read().replace(b'\x00', b'')
    all_lines = content.decode('latin-1').splitlines()

    displacements = {}
    stresses      = {}
    current_block = None

    for line in all_lines:

        # ── Block tespiti ────────────────────────────
        if 'DISP' in line:
            current_block = 'displacement'
            continue
        if 'STRESS' in line:
            current_block = 'stress'
            continue
        if line.strip().startswith('-3'):
            current_block = None
            continue

        if current_block is None:
            continue

        # ── Veri satırı kontrolü ─────────────────────
        # Veri satırları ' -1' ile başlar
        if not line.startswith(' -1'):
            continue

        # ── Sabit kolon ile parse et ─────────────────
        try:
            # Node ID: [3:13]
            node_str = line[3:13].strip()
            if not node_str:
                continue
            node = int(node_str)

            # Değerleri oku: her biri 13 karakter
            def get_val(s, start):
                chunk = s[start:start+13].strip()
                if not chunk:
                    return None
                try:
                    return float(chunk)
                except ValueError:
                    return None

            v1 = get_val(line, 13)
            v2 = get_val(line, 26)
            v3 = get_val(line, 39)
            v4 = get_val(line, 52)
            v5 = get_val(line, 65)
            v6 = get_val(line, 78)

            if current_block == 'displacement':
                # Displacement: 3 değer (ux, uy, uz)
                if v1 is not None and v2 is not None and v3 is not None:
                    displacements[node] = (v1, v2, v3)

            elif current_block == 'stress':
                # Stress: 6 değer (s11, s22, s33, s12, s13, s23)
                # Eğer satırda 6 değer varsa direkt al
                # Eğer 3'er değer 2 satırda geliyorsa biriktir
                vals = [x for x in [v1, v2, v3, v4, v5, v6] if x is not None]
                if node in stresses:
                    # İkinci satır — birleştir ama max 6 değer
                    combined = stresses[node] + tuple(vals)
                    stresses[node] = combined[:6]
                else:
                    stresses[node] = tuple(vals)

        except Exception:
            continue

    print(f"    Parsed {len(displacements)} displacement nodes")
    print(f"    Parsed {len(stresses)} stress nodes")

    if not displacements:
        print("UYARI: Displacement okunamadı!")
        return None

    # ── Von Mises stres hesapla ──────────────────────
    von_mises = {}
    for node, s in stresses.items():
        if len(s) >= 6:
            s11, s22, s33, s12, s13, s23 = s[0], s[1], s[2], s[3], s[4], s[5]
            vm = (0.5 * (
                (s11-s22)**2 + (s22-s33)**2 + (s33-s11)**2 +
                6*(s12**2 + s23**2 + s13**2)
            )) ** 0.5
            von_mises[node] = vm

    # ── Maksimum değerleri bul ───────────────────────
    total_disp     = {n: (ux**2+uy**2+uz**2)**0.5 for n, (ux, uy, uz) in displacements.items()}
    max_disp_node  = max(total_disp, key=total_disp.get)
    max_disp_value = total_disp[max_disp_node]

    max_vm_node  = max(von_mises, key=von_mises.get) if von_mises else None
    max_vm_value = von_mises[max_vm_node] if max_vm_node else 0.0

    return {
        "displacements"    : displacements,
        "von_mises"        : von_mises,
        "max_displacement" : max_disp_value,
        "max_disp_node"    : max_disp_node,
        "max_von_mises"    : max_vm_value,
        "max_vm_node"      : max_vm_node,
        "num_nodes_parsed" : len(displacements)
    }


def print_results(results, material_yield=235.0):

    if results is None:
        print("No results to display.")
        return

    max_vm   = results['max_von_mises']
    max_disp = results['max_displacement']

    safety_factor = material_yield / max_vm if max_vm > 0 else 999.0

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

    base_dir = r"C:\Users\aysal\Desktop\AI_Component_Analyzer\backend\solver"
    inp_file = os.path.join(base_dir, "analysis.inp")
    frd_file = os.path.join(base_dir, "analysis.frd")

    success = run_analysis(inp_file)

    if success:
        results = read_frd_results(frd_file)
        print_results(results, material_yield=235.0)
    else:
        print("\nAnalysis failed. Check the input file.")