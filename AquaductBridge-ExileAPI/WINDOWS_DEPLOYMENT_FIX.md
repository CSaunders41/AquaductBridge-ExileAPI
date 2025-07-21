# 🔧 Windows ExileApi-Compiled Deployment Fix

## ❌ Problem
Your Windows ExileApi-Compiled installation still has the old duplicate files causing build errors:
```
C:\Users\Admin\Documents\POE1\ExileApi-Compiled-3.26.0.0.4\Plugins\Source\AqueductBridge-ExileAPI\
```

## ✅ Solution Options

### Option A: Clean Deploy (Recommended)

1. **Delete the old plugin directory on Windows:**
   ```cmd
   cd "C:\Users\Admin\Documents\POE1\ExileApi-Compiled-3.26.0.0.4\Plugins\Source"
   rmdir /s AqueductBridge-ExileAPI
   ```

2. **Download the fixed version from GitHub:**
   - Go to: https://github.com/CSaunders41/AquaductBridge-ExileAPI
   - Click "Code" → "Download ZIP"
   - Extract to: `C:\Users\Admin\Documents\POE1\ExileApi-Compiled-3.26.0.0.4\Plugins\Source\AqueductBridge-ExileAPI`

### Option B: Git Pull (If you have Git)

```cmd
cd "C:\Users\Admin\Documents\POE1\ExileApi-Compiled-3.26.0.0.4\Plugins\Source\AqueductBridge-ExileAPI"
git pull origin main
```

### Option C: Manual File Cleanup

**Delete these duplicate files/folders from your Windows installation:**
```cmd
cd "C:\Users\Admin\Documents\POE1\ExileApi-Compiled-3.26.0.0.4\Plugins\Source\AqueductBridge-ExileAPI"

# Delete deployment directory copies
rmdir /s AqueductBridge_Deploy_20250720_201333
del AqueductBridge_Deploy_20250720_201333.zip

# Delete any nested AqueductBridge-ExileAPI directories
rmdir /s AqueductBridge-ExileAPI
```

## 🎯 After Cleanup - Build Test

1. **Navigate to the plugin directory:**
   ```cmd
   cd "C:\Users\Admin\Documents\POE1\ExileApi-Compiled-3.26.0.0.4\Plugins\Source\AqueductBridge-ExileAPI"
   ```

2. **Build RadarMovement plugin:**
   ```cmd
   dotnet build RadarMovement.csproj --configuration Release
   ```

3. **Build AqueductBridge plugin:**
   ```cmd
   dotnet build AqueductBridge.csproj --configuration Release
   ```

## 📁 Expected Clean File Structure

After cleanup, your Windows directory should look like:
```
AqueductBridge-ExileAPI/
├── RadarMovement.cs
├── RadarTask.cs
├── RadarMovement.csproj     ← Fixed project file
├── AqueductBridgePlugin.cs
├── AqueductBridgeSettings.cs
├── AqueductBridge.csproj    ← Fixed project file
├── Utils/
│   ├── EventBus.cs
│   ├── LineOfSight.cs
│   ├── AqueductPathfinder.cs
│   └── BinaryHeap.cs
├── aqueduct_automation/     ← Python automation
├── *.py files               ← Python scripts
└── build scripts           ← .bat files
```

## 🚫 What Should NOT Be There

These should be completely gone:
- ❌ `AqueductBridge_Deploy_20250720_201333/` directory
- ❌ `AqueductBridge-ExileAPI/AqueductBridge-ExileAPI/` nested directory
- ❌ Any duplicate .cs files in subdirectories

## ✅ Success Indicators

After successful cleanup and build:
- ✅ No CS0101 duplicate class definition errors
- ✅ Build output: `RadarMovement.dll` in `bin\Release\net8.0\`
- ✅ Build output: `AqueductBridge.dll` in `bin\Release\`

## 🔄 Project References

The project files are configured for your ExileApi-Compiled path:
- ExileCore.dll: `..\..\..\..\ExileCore.dll` 
- Which resolves to: `C:\Users\Admin\Documents\POE1\ExileApi-Compiled-3.26.0.0.4\ExileCore.dll`

If your ExileCore.dll is in a different location, update the `<HintPath>` in the .csproj files. 