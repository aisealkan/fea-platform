# fea_input_writer.py
import gmsh
import os

def generate_calculix_input(step_file_path, material, boundary_conditions, output_dir, mesh_size=5.0):
    
    print("\n" + "="*50)
    print("  FEA INPUT GENERATOR")
    print("="*50)

    # ── Step 1: Mesh ─────────────────────────────────
    print("\n[1/4] Generating mesh...")

    gmsh.initialize()
    gmsh.option.setNumber("General.Verbosity", 1)
    gmsh.model.add("fea_model")
    gmsh.model.occ.importShapes(step_file_path)
    gmsh.model.occ.synchronize()

    gmsh.option.setNumber("Mesh.Algorithm3D", 4)       # Frontal-Delaunay
    gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
    gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size * 0.8)
    gmsh.option.setNumber("Mesh.Optimize", 1)
    gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)

    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.setOrder(1)                        # C3D4 = first order
    gmsh.model.mesh.optimize("Netgen")

    # ── Step 2: Node ve element bilgilerini al ────────
    print("[2/4] Extracting nodes and elements...")

    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()

    nodes = {}
    for i, tag in enumerate(node_tags):
        x = node_coords[i*3]
        y = node_coords[i*3 + 1]
        z = node_coords[i*3 + 2]
        nodes[int(tag)] = (x, y, z)

    # Sadece 3D tetrahedra al (type 4 = C3D4)
    elements = {}
    elem_counter = 1
    elem_types, elem_tags, elem_nodes = gmsh.model.mesh.getElements(dim=3)

    for etype, etags, enodes in zip(elem_types, elem_tags, elem_nodes):
        nodes_per_elem = len(enodes) // len(etags)
        if nodes_per_elem != 4:
            print(f"    UYARI: {nodes_per_elem}-node element bulundu, atlanıyor.")
            continue
        for i, tag in enumerate(etags):
            start = i * 4
            conn  = [int(n) for n in enodes[start:start+4]]
            elements[elem_counter] = conn
            elem_counter += 1

    # Bottom/top node'ları bul
    all_z     = [c[2] for c in nodes.values()]
    min_z     = min(all_z)
    max_z     = max(all_z)
    tol       = mesh_size * 0.1

    bottom_nodes = [t for t, c in nodes.items() if abs(c[2] - min_z) < tol]
    top_nodes    = [t for t, c in nodes.items() if abs(c[2] - max_z) < tol]

    print(f"    Nodes          : {len(nodes):,}")
    print(f"    Elements (C3D4): {len(elements):,}")
    print(f"    Fixed (bottom) : {len(bottom_nodes)}")
    print(f"    Loaded (top)   : {len(top_nodes)}")

    if len(elements) == 0:
        gmsh.finalize()
        raise RuntimeError("Hiç C3D4 element bulunamadı! Mesh oluşturulamadı.")

    gmsh.finalize()

    # ── Step 3: .inp dosyasını yaz ───────────────────
    print("[3/4] Writing CalculiX input file...")

    inp_path = os.path.join(output_dir, "analysis.inp")

    with open(inp_path, 'w', newline='\n') as f:

        f.write("** CalculiX Input File\n")
        f.write("** Element type: C3D4 (4-node tetrahedron, first order)\n\n")

        # NODES
        f.write("*NODE, NSET=ALL_NODES\n")
        for tag, (x, y, z) in nodes.items():
            f.write(f"{tag}, {x:.6f}, {y:.6f}, {z:.6f}\n")

        # ELEMENTS — C3D4 !
        f.write("\n*ELEMENT, TYPE=C3D4, ELSET=ALL_ELEMENTS\n")
        for tag, conn in elements.items():
            f.write(f"{tag}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}\n")

        # FIXED NODE SET
        f.write("\n*NSET, NSET=FIXED_NODES\n")
        for i, n in enumerate(bottom_nodes):
            f.write(str(n))
            f.write("\n" if (i+1) % 10 == 0 else ", ")
        f.write("\n")

        # LOAD NODE SET
        f.write("\n*NSET, NSET=LOAD_NODES\n")
        for i, n in enumerate(top_nodes):
            f.write(str(n))
            f.write("\n" if (i+1) % 10 == 0 else ", ")
        f.write("\n")

        # MATERIAL
        f.write(f"\n*MATERIAL, NAME={material['name']}\n")
        f.write("*ELASTIC\n")
        f.write(f"{material['youngs_modulus']}, {material['poisson_ratio']}\n")
        f.write("*DENSITY\n")
        f.write(f"{material['density']}\n")

        # SECTION
        f.write(f"\n*SOLID SECTION, ELSET=ALL_ELEMENTS, MATERIAL={material['name']}\n\n")

        # STEP
        f.write("*STEP\n")
        f.write("*STATIC\n\n")

        # BOUNDARY CONDITIONS
        f.write("*BOUNDARY\n")
        f.write("FIXED_NODES, 1, 3, 0.0\n\n")

        # FORCE
        force_total    = boundary_conditions['force_z']
        force_per_node = force_total / len(top_nodes)
        f.write(f"** Total force: {force_total} N across {len(top_nodes)} nodes\n")
        f.write("*CLOAD\n")
        for n in top_nodes:
            f.write(f"{n}, 3, {force_per_node:.6f}\n")

        # OUTPUT
        f.write("\n*NODE FILE\nU\n")
        f.write("*EL FILE\nS\nE\n")
        f.write("\n*END STEP\n")

    print(f"    Saved: {inp_path}")
    return inp_path, len(nodes), len(elements)


if __name__ == "__main__":

    steel = {
        "name"           : "STEEL",
        "youngs_modulus" : 210000,
        "poisson_ratio"  : 0.3,
        "density"        : 7.85e-9,
        "yield_strength" : 235
    }

    loads = {"force_z": -10000}

    step_file  = r"C:\Users\aysal\Desktop\AI_Component_Analyzer\test_part.step"
    output_dir = r"C:\Users\aysal\Desktop\AI_Component_Analyzer"

    inp_file, n_nodes, n_elems = generate_calculix_input(
        step_file_path      = step_file,
        material            = steel,
        boundary_conditions = loads,
        output_dir          = output_dir,
        mesh_size           = 5.0
    )

    print(f"\n✓ Hazır: {inp_file}")
