# <img src="icons/app_icon.png" alt="4000 Weeks app icon." width="50"/> 4000 Weeks
4000 Weeks is a lightweight app based on Oliver Burkeman's book of the same name which visualises
80 years as a grid of weeks. 
# Overview
## Description
The 4000 Weeks app is your interactive diary for your life. Each time you open the app, your life is represented with all of the weeks you have lived, the present week you are in, and all of your weeks to come. For each week that you have lived, you can add information which will populate the grid with what happened that week: type, up to four images and a text description.


Despite this confronting number of weeks that the average person lives, this app aims to help 
remember your experiences, relive happy memories, and celebrate life.

## Status
Complete

## Tech Stack

**Language:** Python 3.14

**Dependencies:**
- `Pillow` (10.1.0) - Image processing
- `json` (1.1.3) - JSON file reading and writing

**Standard Library:**
- `tkinter` - GUI framework
- `os` - File system operations
- `datetime` - Date handling
- `shutil` - File system operations

## Installation
### Requirements
- Pillow     == 12.3.0

## Features
### Functionality
#### Project Tools
- `Open` - Load a locally saved 4000 Week file.
- `Save` - Save the current 4000 Week file.
- `Theme Toggle` - Toggle the UI theme between light mode and dark mode.
- `Update Birthday` - Open a popup to enter a new birthday to visualise 'DD-MM-YYYY'.

#### Week Information
- `Week Category` - A list of categories to select from to summarise the events of that week.
- `Images` - Upload 0-4 images per week of the events that happened in that week.
- `Description` - A multi-line text entry to capture the details of the events that week.

## Screenshots
Using the colour code format drop down.


![Swatch software showing the colour code dropdown UI.](readme_images/swatch_colour_format_dropdown.png "Colour format dropdown")

Mouse hover hint text for copying.


![Swatch software showing the hint text to copy a colour code.](readme_images/swatch_copy_hint.png "Copy hint text")

Delete project popup.


![Swatch software showing the delete project confirmation popup.](readme_images/swatch_delete_project_popup.png "Delete project confirmation popup")

Mouse hover hint text for colour formatting.


![Swatch software showing the hint text when formatting the colour code.](readme_images/swatch_hover_hint_format.png "Formatting the colour code")

Adding a new swatch colour popup.


![Swatch software showing the add new swatch popup UI.](readme_images/swatch_new_swatch.png "Create swatch popup")

Tint adjustment for all colour swatch cards.


![Swatch software showing the tint adjustment tool in action.](readme_images/swatch_tint_adjustment.png "Tint adjustment tool")

## Author
**Kelton Boyter-Grant**  

**AI Disclosure:**  
The use if artificial intelligence (AI) has been used to aid the development of this project. All AI code has been reviewed and approved by a human before integration with the the code base.
