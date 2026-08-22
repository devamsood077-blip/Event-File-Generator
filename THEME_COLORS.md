# Theme Color Reference

This document lists all the hex color codes used in the Event File Generator GUI. You can customize these colors by editing the `setup_theme()` method in `event_folder_generator.py`.

## Color Sections

### Dark Theme Colors

Located in `event_folder_generator.py` lines 69-85:

```python
'bg_main': '#1e1e1e',           # Main background - Window and main frame background
'bg_frame': '#252526',          # Frame background - Secondary frame backgrounds
'bg_entry': '#3c3c3c',          # Entry field background - Text input fields
'bg_button': '#0e639c',         # Button background - All button backgrounds
'bg_button_hover': '#1177bb',  # Button hover - Button hover state
'fg_text': '#cccccc',          # Text color - General text and status messages
'fg_label': '#ffffff',         # Label text color - All section labels
'fg_entry': '#cccccc',         # Entry text color - Text inside input fields
'border': '#3c3c3c',           # Border color - Entry and combobox borders
'accent': '#0078d4',           # Accent color - Progress bar and highlights
'status_success': '#4ec9b0',   # Success status color - Success messages
'status_error': '#f48771',     # Error status color - Error messages
'status_warning': '#ce9178',   # Warning status color - Warning messages
```

### Light Theme Colors

Located in `event_folder_generator.py` lines 86-102:

```python
'bg_main': '#ffffff',          # Main background - Window and main frame background
'bg_frame': '#f3f3f3',         # Frame background - Secondary frame backgrounds
'bg_entry': '#ffffff',         # Entry field background - Text input fields
'bg_button': '#0078d4',        # Button background - All button backgrounds
'bg_button_hover': '#106ebe',  # Button hover - Button hover state
'fg_text': '#323130',          # Text color - General text and status messages
'fg_label': '#201f1e',        # Label text color - All section labels
'fg_entry': '#323130',        # Entry text color - Text inside input fields
'border': '#edebe9',          # Border color - Entry and combobox borders
'accent': '#0078d4',          # Accent color - Progress bar and highlights
'status_success': '#107c10',  # Success status color - Success messages
'status_error': '#d13438',    # Error status color - Error messages
'status_warning': '#ffaa44',  # Warning status color - Warning messages
```

## Where Each Color is Used

### bg_main (Main Background)
- Root window background
- Main frame background
- All label backgrounds

### bg_frame (Frame Background)
- Secondary frames (template_frame, dest_frame, overlay_frame)
- Progress bar trough

### bg_entry (Entry Background)
- All text entry fields
- Combobox fields

### bg_button (Button Background)
- All buttons (Browse, Refresh, Clear, Generate, Preview)

### bg_button_hover (Button Hover)
- Button hover state (when mouse is over button)

### fg_text (Text Color)
- Status label default text
- General informational text

### fg_label (Label Text Color)
- All section labels:
  - "Template Folder Location:"
  - "Event Type:"
  - "Template:"
  - "Destination Folder:"
  - "Event Base:"
  - "Event Name:"
  - "Overlay Image (optional):"

### fg_entry (Entry Text Color)
- Text inside all input fields
- Text inside comboboxes
- Combobox arrow color

### border (Border Color)
- Entry field borders
- Combobox borders

### accent (Accent Color)
- Progress bar fill
- "Copying files..." status message

### status_success (Success Color)
- "Found X template(s)" messages
- "Found X subfolder(s)" messages
- "Successfully created..." messages

### status_error (Error Color)
- "Template folder not found"
- "Permission denied" messages
- "Error occurred" messages

### status_warning (Warning Color)
- "No templates found"
- "No subfolders found" messages

## How to Customize Colors

1. Open `event_folder_generator.py`
2. Find the `setup_theme()` method (around line 67)
3. Locate the theme you want to customize (dark or light)
4. Change the hex codes to your desired colors
5. Save and run the application

Example:
```python
# Change main background to a custom color
'bg_main': '#2a2a2a',  # Your custom color
```

## Color Format

All colors use hexadecimal format: `#RRGGBB`
- `#` - Required prefix
- `RR` - Red component (00-FF)
- `GG` - Green component (00-FF)
- `BB` - Blue component (00-FF)

Example: `#0078d4` = Blue color (Windows accent blue)
