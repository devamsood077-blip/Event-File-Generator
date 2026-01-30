# Event File Generator

A simple Windows GUI tool to create new event folders by copying files from template folders.

## Features

- **Template Selection**: Dropdown menu to select from available template folders
- **Custom Naming**: Enter a custom name for your new event folder
- **Recursive Copying**: Automatically copies all files and subfolders from the template
- **Easy to Use**: Simple graphical interface built with Python tkinter

## Requirements

- Windows 10 or later
- Python 3.6 or higher (usually pre-installed on Windows 10/11)

## Installation

1. Make sure Python is installed on your system
   - Check by opening Command Prompt and typing: `python --version`
   - If not installed, download from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"

2. No additional packages needed! The tool uses only Python's built-in libraries.

## Usage

### Quick Start

1. **Double-click** `run_event_generator.bat` to launch the application

   OR

2. **Run from command line**:
   ```bash
   python event_folder_generator.py
   ```

### Step-by-Step Guide

1. **Set Template Folder Location**
   - Click "Browse" next to "Template Folder Location"
   - Navigate to the folder containing your template folders (AI Removal, BnW, Color, etc.)
   - Click "Select Folder"
   - Click "Refresh" to scan for available templates

2. **Select Template**
   - Choose a template from the dropdown menu (e.g., "AI Removal", "Color", "Greenscreen")

3. **Set Destination Folder**
   - Click "Browse" next to "Destination Folder"
   - Select where you want the new event folder to be created
   - Click "Select Folder"

4. **Enter Folder Name**
   - Type the name for your new event folder (e.g., "Wedding_2024_01_15")

5. **Generate Folder**
   - Click "Generate Event Folder"
   - Wait for the copy process to complete
   - You'll see a success message with an option to open the new folder

## How It Works

The tool:
1. Scans the template folder for available template directories
2. When you click "Generate Event Folder", it:
   - Creates a new folder with your custom name in the destination location
   - Recursively copies all files and subfolders from the selected template
   - Preserves the entire directory structure

## Example

If your template folder structure is:
```
Templates/
  ├── AI Removal/
  │   ├── Event Files/
  │   │   ├── file1.jpg
  │   │   └── file2.png
  │   └── config.txt
  └── Color/
      └── ...
```

And you:
- Select template: "AI Removal"
- Enter folder name: "Smith_Wedding_2024"
- Set destination: "C:\Events"

The result will be:
```
C:\Events\
  └── Smith_Wedding_2024/
      ├── Event Files/
      │   ├── file1.jpg
      │   └── file2.png
      └── config.txt
```

## Troubleshooting

### "Python is not installed or not in PATH"
- Install Python from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"
- Restart your computer after installation

### "Template folder not found"
- Make sure the template folder path is correct
- Click "Browse" to select the correct folder
- Click "Refresh" to rescan for templates

### "Permission denied"
- Make sure you have read access to the template folder
- Make sure you have write access to the destination folder
- Try running as administrator if needed

### Folder already exists
- The tool will ask if you want to overwrite
- If you choose "Yes", the existing folder will be deleted and replaced
- Be careful: this action cannot be undone!

## Notes

- The tool preserves the exact folder structure from templates
- All files and subfolders are copied recursively
- The copy process runs in a separate thread to keep the UI responsive
- Large folders may take some time to copy - be patient!
