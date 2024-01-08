# NoSnoop: Yet another P2P anonymous chat apps

**Advantages:**

- 👥 Peer to peer, no single source of truth
- 🧅 All communication is routed through TOR
- 🔒 Besides traffic, every single chat file is encrypted with a password
- 🔑 No need for a phone number with TOR based authentication
- 🗑️ Duress codes, both local and remote. Delete your data without anyone knowing.
- 📄 General file sharing support
- 🤷 No leaks, the only one that owns the data is you and your recipient
- 👁️ Open source, everyone can look up what's in the application

**Setup**:

If you are too lazy to compile the program here's what to do:

- Download the build for your platform from Github Action's artifacts and install Tor (if not already done).
- Adjust the config file to your needs (it's **REALLY** recommended that you set the browser field in the config to the path of a privacy respecting browser like [Ungoogled Chromium](https://ungoogled-software.github.io/ungoogled-chromium-binaries/))

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

**It's slow**:

I already know. All the messages get routed through TOR, so it's slow because of bouncing the request through multiple destinations instead of just one recipient machine. Plus, all messages are locally encrypted, so everytime that a chat has to be read or wrote to some time elapses because of computational limits (tl;dr: encryption/de-encryption takes some time). If you prioritize speed over privacy and anonymity I'd suggest to try other messaging apps such as [Signal](https://signal.org)

**Bottom page**:

Still in early development. Made with ❤️ and with privacy in mind by Andrea Licheri
