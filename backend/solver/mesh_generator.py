# mesh_generator.py
# Takes geometry from STEP reader and creates a mesh for FEA

import gmsh
import os
import sys

def generate_mesh(step_file_path, mesh_size=5.0):
    """
    Reads a STEP file and generates a 3D mesh.
    
    Parameters:
        step_file_path : path to the .step file
        mesh_size      : controls how fine the mesh is (smaller = finer = slower)
                         5.0 means roughly 5mm between mesh points
    
    Returns:
        Dictionary with mesh statistics and output file path
    """
    
    print("\n=== Mesh Generator Started ===")
    print(f"Input file  : {step_file_path}")
    print(f"Mesh size   : {mesh_size} mm")
    
    # Check file exists
    if not os.path.exists(step_file_path):
        print(f"ERROR: File not found: {step_file_path}")
        return None
    
    # Initialize GMSH
    # GMSH is the meshing engine we installed earlier
    gmsh.initialize()
    
    # Suppress GMSH's own output messages (we'll print our own)
    gmsh.option.setNumber("General.Verbosity", 1)
    
    # Create a new GMSH model
    gmsh.model.add("fea_model")
    
    print("Loading geometry into mesh engine...")
    
    # Import the STEP file directly into GMSH
    gmsh.model.occ.importShapes(step_file_path)
    
    # Synchronize: tell GMSH to process what we just loaded
    gmsh.model.occ.synchronize()
    
    print("Geometry loaded. Setting mesh parameters...")
    
    # Set global mesh size
    # This controls how densely the mesh covers the geometry
    gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
    gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size * 0.5)
    
    # Set mesh algorithm
    # Algorithm 1 = Delaunay (reliable for most geometries)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    
    print("Generating 3D mesh... (this may take a few seconds)")
    
    # Generate the mesh
    # 3 means 3-dimensional mesh (tetrahedra)
    gmsh.model.mesh.generate(3)
    
    print("Mesh generated. Collecting statistics...")
    
    # Get mesh statistics
    # Node = a point in the mesh (what we called "dugum" / node)
    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
    num_nodes = len(node_tags)
    
    # Element = a small piece of the geometry (tetrahedron)
    element_types, element_tags, _ = gmsh.model.mesh.getElements()
    num_elements = sum(len(tags) for tags in element_tags)
    
    # Define output file path
    output_dir  = os.path.dirname(step_file_path)
    output_file = os.path.join(output_dir, "mesh_output.msh")
    
    # Save the mesh to a file
    # .msh is GMSH's native format, CalculiX can read this
    gmsh.write(output_file)
    
    print(f"Mesh saved to: {output_file}")
    
    # Clean up GMSH
    gmsh.finalize()
    
    result = {
        "num_nodes"    : num_nodes,
        "num_elements" : num_elements,
        "mesh_size"    : mesh_size,
        "output_file"  : output_file
    }
    
    return result


def print_mesh_summary(data):
    """Prints mesh statistics in a readable format"""
    
    if data is None:
        print("No mesh data.")
        return
    
    print("\n" + "="*40)
    print("  MESH SUMMARY")
    print("="*40)
    print(f"  Nodes     : {data['num_nodes']:,}")
    print(f"  Elements  : {data['num_elements']:,}")
    print(f"  Mesh size : {data['mesh_size']} mm")
    print(f"  Saved to  : {data['output_file']}")
    print("="*40)


if __name__ == "__main__":
    
    step_file = r"C:\Users\aysal\Desktop\AI_Component_Analyzer\test_part.step"
    
    mesh_data = generate_mesh(step_file, mesh_size=5.0)
    print_mesh_summary(mesh_data)