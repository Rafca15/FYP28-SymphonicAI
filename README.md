# Symphonic AI - MIDI Chatbot 🎹

An interactive web application for live MIDI melody generation and AI-powered continuation, built with Streamlit.

## 🚀 Features

-  Live MIDI input via a virtual or external keyboard
-  Audio playback of user input and AI-generated continuations
-  Session history to review and compare generated melodies
-  MIDI export and ZIP download functionality
-  Temperature control slider to adjust generation randomness
-  Auto-refresh for live interaction without manual page reloads
-  "Generate from Blank" feature for starting without user input
-  Clear history button for session management

---

##  Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/symphonic-ai.git
cd symphonic-ai
```
### 2. Install Dependencies
We recommend using a virtual environment:

```bash
python -m venv venv #(or conda)
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```
### 2.1 Installing FluidSynth on Windows

FluidSynth is a real-time software synthesizer used to render MIDI files into audio, leveraging the SoundFont (.sf2) library. Since FluidSynth is not available via `pip`, on Windows it is easiest to install it with Chocolatey, the Windows package manager.

1. **Install Chocolatey**  
   Open PowerShell _as Administrator_ and run:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
Install FluidSynth
Once Chocolatey is available, install FluidSynth with:

```powershell

choco install fluidsynth -y
```

### 3. Prepare the SoundFont File (SF2)

The SoundFont file (.sf2) is a digital instrument library used to synthesize audio from MIDI files. This project converts generated MIDI into playable audio using a predefined SoundFont.

How to Set It Up
Download a General MIDI SoundFont (e.g., FluidR3_GM.sf2 or another compatible file).

Place the file in the project's root directory or the path specified in config.py as SF2_PATH.
Make sure SF2_PATH in config.py points to the correct location, for example

```python
SF2_PATH = "FluidR3_GM.sf2"

## we recommend putting your sf2 file in the asset folder
```

 Running the App
Navigate to the front end directory, and run:
```bash
python -m http.server 8000 ##(or whatever port is specified in config.py)
```

After completing the setup, start another terminal, you can start the application by running:
```py
streamlit run app.py ##ensure you are in the correct directory
```
Open the provided local URL in your web browser to access the interface.

⚙️ Configuration
Adjust configuration values in config.py as needed, such as:
```
HTTP_HOST: Host address for the MIDI server.

HTTP_PORT: Port for the MIDI server.

SF2_PATH: Path to the SoundFont (.sf2) file.

BROWSER_APP_URL: URL for the embedded MIDI keyboard interface.
```

### License
MIT License. See LICENSE for details.



Streamlit for the web framework
