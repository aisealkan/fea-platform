#fileları check ediyoruz ...

def check_environment():
    print("=== FEA Platform - Environment Check ===")
    
    import sys
    print(f"Python version: {sys.version}")
    
    import os
    folders = ["api", "cad", "solver"]
    for folder in folders:
        if os.path.exists(folder):
            print(f"[OK] {folder}/ folder exists")
        else:
            print(f"[MISSING] {folder}/ folder not found")
            
    
    print("=== Check Complete ===")

check_environment()