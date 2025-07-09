

# Stinger Chroma-Remover (Initial Release)

A user-friendly desktop tool, built with Python, to create transparent `.webm` stinger transitions for OBS, vMix, and other streaming software. This application allows you to visually pick a color to remove (chroma key), fine-tune the quality, and export a ready-to-use video file with an alpha channel.

-----

## \#\# Features

  * **Visual Color Picker**: Click directly on the video preview to select the exact color to make transparent.
  * **High-Quality Output**: Converts to `.webm` (VP9) format with a transparent alpha channel.
  * **Quality Filters**: Includes **Denoise** and **Despill** options to create a cleaner, more professional key.
  * **GPU Acceleration**: Utilizes NVIDIA (CUDA), Intel (QSV), or AMD GPUs to speed up video decoding.
  * **Advanced Controls**: Fine-tune the final output with settings for CRF (quality), encoder speed, resolution, and framerate.
  * **Portable & Smart**: Automatically detects `ffmpeg.exe` if it's in the same folder, making the application portable.
  * **Multi-Language Support**: Easily add new languages by creating simple `.json` files.

-----

## \#\# Installation & Setup

Follow these steps to get the application running on your system.

### \#\#\# 1. Prerequisites

  * **Python 3.9+**: Make sure you have Python installed. You can get it from [python.org](https://www.python.org/).
  * **FFmpeg**: This is required for all video processing.

### \#\#\# 2. Install FFmpeg

You must have FFmpeg on your system. You have two options:

**Option A: Portable (Recommended)**

1.  Download a **static build** of FFmpeg from [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (use a `full` release build).
2.  Unzip the downloaded file.
3.  Find `ffmpeg.exe` inside the `bin` folder.
4.  Copy and paste the `ffmpeg.exe` file into the **same folder as the `index.py` script**.

The application will automatically detect and use it.

**Option B: System-Wide Installation**

Install FFmpeg and add it to your system's PATH.

  * **Windows**: Follow this [Windows installation guide](https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/).


### \#\#\# 3. Install Python Libraries

Open your terminal or command prompt and run the following command to install the necessary Python packages:

```bash
pip install customtkinter opencv-python Pillow
```

-----

## \#\# Running the Application

Once you have completed the setup, you can run the application with this command:

```bash
python index.py
```

-----

## \#\# How to Use

1.  **Step 1: Select Video**: Click the `Select Video File...` button to load your `.mp4` or other source video. A preview will appear on the left.
2.  **Step 2: Pick Color**: Click on the color in the preview image that you want to remove. The color swatch on the right will update.
3.  **Refine Settings (Optional)**:
      * **Quality Tab**: Adjust sliders for **Denoise** or check the **Despill** box to improve your key.
      * **Advanced Tab**: Change resolution, video quality (CRF), encoder speed, or framerate for more control.
4.  **Step 3: Save File**: Click the `Save As WEBM...` button to choose a location and filename for your final transparent video. The conversion will start automatically.

-----


## \#\# Adding Languages (Localization)

You can easily add new translations to the app.

1.  Go to the `languages` folder.
2.  Copy `en.json` and rename it to your language's code (e.g., `fr.json` for French).
3.  Open the new file in a text editor.
4.  Change the `"language_name"` value to the full name of the language (e.g., `"Français"`).
5.  Translate all the other string values in the file.

The next time you run the application, your new language will automatically appear in the dropdown menu.

-----

## \#\# License

This project is licensed under the MIT License.