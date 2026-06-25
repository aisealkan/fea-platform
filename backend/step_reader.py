# step_reader.py
# Reads STEP files and extracts geometry information

import cadquery as cq
import os

def read_step_file(file_path):
    print(f"\nReading: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return None
    
    shape = cq.importers.importStep(file_path)
    print("File loaded successfully.")
    
    solid    = shape.val()
    faces    = shape.faces().size()
    edges    = shape.edges().size()
    vertices = shape.vertices().size()
    
    bb     = solid.BoundingBox()
    width  = round(bb.xmax - bb.xmin, 2)
    depth  = round(bb.ymax - bb.ymin, 2)
    height = round(bb.zmax - bb.zmin, 2)
    volume = round(solid.Volume(), 2)
    
    return {
        "faces"      : faces,
        "edges"      : edges,
        "vertices"   : vertices,
        "width_mm"   : width,
        "depth_mm"   : depth,
        "height_mm"  : height,
        "volume_mm3" : volume,
        "shape"      : shape
    }


def print_summary(data):
    if data is None:
        print("No data.")
        return
    
    print("\n" + "="*40)
    print("  GEOMETRY SUMMARY")
    print("="*40)
    print(f"  Faces    : {data['faces']}")
    print(f"  Edges    : {data['edges']}")
    print(f"  Vertices : {data['vertices']}")
    print(f"  Width    : {data['width_mm']} mm")
    print(f"  Depth    : {data['depth_mm']} mm")
    print(f"  Height   : {data['height_mm']} mm")
    print(f"  Volume   : {data['volume_mm3']} mm³")
    print("="*40)


if __name__ == "__main__":
    test_file = r"C:\Users\aysal\Desktop\AI_Component_Analyzer\test_part.step"
    geometry  = read_step_file(test_file)
    print_summary(geometry)