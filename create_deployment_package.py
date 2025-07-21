#!/usr/bin/env python3
"""
Create Deployment Package for ExileApi-Compiled
Packages all necessary files for deployment and testing
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

def create_deployment_package():
    """Create a deployment package with all necessary files"""
    
    print("📦 Creating Deployment Package for ExileApi-Compiled")
    print("=" * 60)
    
    # Create deployment directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    deployment_name = f"AqueductBridge_Deploy_{timestamp}"
    deployment_dir = Path(deployment_name)
    
    if deployment_dir.exists():
        shutil.rmtree(deployment_dir)
    deployment_dir.mkdir()
    
    print(f"📁 Creating deployment directory: {deployment_name}")
    
    # Files to include in deployment
    files_to_copy = [
        # C# Plugin files
        ("AqueductBridgePlugin.cs", "AqueductBridge/AqueductBridgePlugin.cs"),
        ("AqueductBridgeSettings.cs", "AqueductBridge/AqueductBridgeSettings.cs"), 
        ("AqueductBridge.csproj", "AqueductBridge/AqueductBridge.csproj"),
        ("AqueductBridge.sln", "AqueductBridge/AqueductBridge.sln"),
        ("build.bat", "AqueductBridge/build.bat"),
        
        # Documentation
        ("README_AqueductBridge.md", "AqueductBridge/README.md"),
        ("INSTALLATION.md", "AqueductBridge/INSTALLATION.md"),
        ("IMPLEMENTATION_SUMMARY.md", "AqueductBridge/IMPLEMENTATION_SUMMARY.md"),
        
        # Python automation system
        ("requirements.txt", "Python_Automation/requirements.txt"),
        ("start_automation.py", "Python_Automation/start_automation.py"),
        ("start_automation.bat", "Python_Automation/start_automation.bat"),
        ("debug_coordinate_fixes.py", "Python_Automation/debug_coordinate_fixes.py"),
        
        # Test scripts  
        ("test_coordinates.py", "Python_Automation/test_coordinates.py"),
        ("debug_movement.py", "Python_Automation/debug_movement.py"),
        ("test_all_systems.py", "Python_Automation/test_all_systems.py"),
    ]
    
    # Copy individual files
    for src_file, dst_path in files_to_copy:
        src_path = Path(src_file)
        dst_full_path = deployment_dir / dst_path
        
        # Create parent directories
        dst_full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if src_path.exists():
            shutil.copy2(src_path, dst_full_path)
            print(f"  ✅ Copied: {src_file}")
        else:
            print(f"  ⚠️  Missing: {src_file}")
    
    # Copy entire aqueduct_automation directory
    automation_src = Path("aqueduct_automation")
    automation_dst = deployment_dir / "Python_Automation" / "aqueduct_automation"
    
    if automation_src.exists():
        shutil.copytree(automation_src, automation_dst)
        print(f"  ✅ Copied: aqueduct_automation/ -> Python_Automation/aqueduct_automation/")
    else:
        print(f"  ⚠️  Missing: aqueduct_automation/")
    
    # Create deployment instructions
    instructions = f"""# AqueductBridge Deployment Package
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## CRITICAL FIX: Coordinate Inversion for Backwards Movement

The bot was running backwards due to coordinate inversion. This package includes fixes:

### Quick Fix for Backwards Movement:
1. The coordinate system now has `invert_y=True` by default
2. Use `debug_coordinate_fixes.py` to test different combinations
3. Most common fix: Y-axis needs to be inverted

## Deployment Instructions:

### 1. Deploy ExileAPI Plugin:
```bash
# Copy the AqueductBridge/ folder to:
ExileApi-Compiled/Plugins/Source/AqueductBridge/

# Or copy the compiled DLL to:
ExileApi-Compiled/Plugins/Compiled/AqueductBridge.dll
```

### 2. Setup Python Automation:
```bash
# Extract Python_Automation/ to any directory
cd Python_Automation
pip install -r requirements.txt
```

### 3. Test Coordinate Fixes:
```bash
# Run this FIRST to diagnose coordinate issues:
python debug_coordinate_fixes.py

# Then run normal automation:
python start_automation.py
```

## Troubleshooting Backwards Movement:

If bot still runs backwards:
1. Run `debug_coordinate_fixes.py`
2. Test different coordinate fixes (option 2 is usually correct)
3. Option 2 (invert_y) should fix most backwards movement issues

## Common Coordinate Fixes:
- `invert_y=True` - Fixes moving up instead of down (MOST COMMON)
- `invert_x=True` - Fixes moving left instead of right  
- `swap_xy=True` - Fixes if X and Y are swapped

## Testing:
1. Load Path of Exile (Windowed mode)
2. Start ExileAPI with AqueductBridge enabled
3. Enter any area (Aqueducts recommended)
4. Run `debug_coordinate_fixes.py` to find correct settings
5. Run `start_automation.py` with fixed coordinates

The coordinate fix is already set to `invert_y=True` which should fix the backwards movement issue.
"""
    
    # Write instructions
    with open(deployment_dir / "DEPLOYMENT_INSTRUCTIONS.txt", "w") as f:
        f.write(instructions)
    print(f"  ✅ Created: DEPLOYMENT_INSTRUCTIONS.txt")
    
    # Create zip file
    zip_path = Path(f"{deployment_name}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in deployment_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(deployment_dir)
                zipf.write(file_path, arcname)
    
    print(f"\n📦 Created deployment package: {zip_path}")
    print(f"📊 Package size: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    # Show contents
    print(f"\n📋 Package contents:")
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        for info in zipf.filelist:
            print(f"  📄 {info.filename}")
    
    print("\n" + "=" * 60)
    print("✅ DEPLOYMENT PACKAGE READY!")
    print("=" * 60)
    print(f"📁 Folder: {deployment_dir}")
    print(f"📦 Zip: {zip_path}")
    print("\n🔧 KEY FIX: Coordinate system set to invert_y=True")
    print("   This should fix the backwards movement issue!")
    print(f"\n📖 Read DEPLOYMENT_INSTRUCTIONS.txt for setup details")
    
    # Clean up directory (keep zip)
    response = input(f"\nDelete temporary folder {deployment_dir}? (y/N): ").strip().lower()
    if response == 'y':
        shutil.rmtree(deployment_dir)
        print(f"🗑️ Deleted temporary folder")
    
    return zip_path

if __name__ == "__main__":
    try:
        zip_path = create_deployment_package()
        print(f"\n🎯 Ready to deploy: {zip_path}")
    except Exception as e:
        print(f"\n❌ Error creating deployment package: {e}")
        import traceback
        traceback.print_exc() 