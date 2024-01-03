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

- Clone this repo
- Install TOR and your favourite flavour of private Chromium if not already done
- Install dependencies with `pip install -r requirements.txt`
- (Optional but reccomended); Build with [pyinstaller](https://pyinstaller.org/en/stable/)
- Adjust the config file to your needs
- Open it and set a password. **Choose a password that you'll remember well. There are no means of recovery if you don't**

**Usage**:

Get the other person hash through other means of communication (preferably physical ones). Insert the hash in the "New Chat" box and click on the newly created chat.

**Disadvantages**:

- Slow, between local encryption and TOR routing
- Still in early development
