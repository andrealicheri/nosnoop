# NoSnoop: Yet another P2P anonymous chat app

**Advantages:**

- 👥 Fully P2P
- 🧅 TOR-routed communication
- 🔒 Chats encrypted both locally with password and E2E with keys
- 🔑 No phone number, email or other jargon
- 🗑️ Duress codes, both local and remote
- 📄 File Sharing support
- 👁️ Open source
- 🤏 Extremely minimal codebase

**Setup**:

If you are too lazy to compile the program here's what to do:

- Download the build for your platform from Github Action's artifacts and install Tor (if not already done).
- In the `config.json` file, adjust the `tor` and `browser` fields so that they point to your tor installations (usually `{The folder where you installed Tor Browser}/TorBrowser/Tor/tor.exe` on Windows) and to your browser of choice respectively (it's **REALLY** recommended that you set the `browser` field in the config to point to a privacy respecting browser like [Ungoogled Chromium](https://ungoogled-software.github.io/ungoogled-chromium-binaries/)) 

**Building**:

The best way to verify that an application is secure is by checking the code manually and compiling it yourself. Here's how to do it:

- Clone the repo and check for any tampering that goes out of the scope of the application
- Once you've verified the integrity of the application is very important to compile it. This will prevent malicious software installed on your machine to modify and backdoor the code.
- Install the project dependencies (`pip install -r requirements.txt`) plus pyinstaller (`pip install pyinstaller`).
- Run the following command:
  - Windows: `pyinstaller --onefile --add-data "app;app" --hidden-import _cffi_backend app.py`
  - UNIX: `pyinstaller --onefile --add-data "app:app" --hidden-import _cffi_backend app.py`
- Go to `dist/` and find your binary.

**Usage**:

- Cut and open the program in a dedicated folder
- **Choose a password that you will remember well. There are no means of recovery if you don't.**
- Get the other person hash through other means of communication (preferably physical ones).
- Insert the hash in the "New Chat" box
- Click on the newly created chat.

**Limitations**:

- Python -> Encryption -> TOR traffic -> Python -> OTP verification -> Decryption makes the app really slow
- The app only works if both clients are connected at the same time, as it is fully P2P with no STUN servers used
- Small codebase from a small developer means risk of unmantained code
- Uses obscure "requests_tor" lib which is unmantained since 2022 

**Tech stack**:
- Python and Flask for handling traffic between peers
- NaCl (Curve25519) for E2E encryption and PBKDF2 for local storage encryption
- requests_tor for handling tor requests
- Basic HTMLCSS for the UI (along with htmx.js to handle routing)
- Flaskwebgui to wrap app() server route in the browser