from flask import Flask  
from flask import send_from_directory, request, redirect, abort, Response, stream_with_context
from flaskwebgui import FlaskUI 
import os
import subprocess
import time
from nacl.public import PrivateKey, PublicKey, SealedBox
from nacl.secret import SecretBox
import nacl.utils
from pbkdf2 import PBKDF2
import requests
import threading
from requests_tor import RequestsTor
import secrets
import bleach
import base64
import mimetypes
import shutil
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from nacl.bindings import crypto_sign_ed25519_sk_to_curve25519
from nacl.bindings import crypto_sign_ed25519_pk_to_curve25519
import sys


# No config.json exist means that browser and tor are not pointed for the program
if not os.path.exists("config.json"):
   with open("config.json", "w") as f:
      f.write("""{
    "browser": "Put your browser of choice executable path here",
    "tor": "tor",
    "torPort": 32022,
    "receivePort": 32023
}""")
   input("config.json generated to be edited. Press Enter to quit.")
   sys.exit(0)

# Loads config.json
with open("config.json", "r") as f:
   config = json.load(f)

if shutil.which(config["browser"]) is None:
   print("No browser to display the UI!")
   print("Please, set the browser field in config.json to point to an executable of a browser you trust.")
   input("Press Enter to quit.")
   sys.exit(0)

def create(folders):
   for folder in folders:
      if not os.path.exists(folder):
         os.mkdir(folder)

# First boot
create(["data/", "data/chats", "data/codes"])

# Configures persistent tor address
if not os.path.exists("data/.torrc"):
   with open("data/.torrc", "w") as f:
      f.write(rf"""HiddenServiceDir {os.path.abspath("data/")}
HiddenServicePort 80 127.0.0.1:{config["receivePort"]}
SOCKSPort {config["torPort"]}""")

# Updates .torrc if config.json is changed  
else:
   with open("data/.torrc", "r") as f:
      content = f.readlines()
      content[1] = f"HiddenServicePort 80 127.0.0.1:{config["receivePort"]}"
      content[2] = f"\nSOCKSPort {config["torPort"]}"
   with open("data/.torrc", "w") as f:
      f.writelines(content)

 # Not actually concerned with any tor bugs, just delays crash in case tor is not installed
 # See app.route("/")
try: 
   process = subprocess.Popen([config["tor"], "-f", os.path.abspath("data/.torrc")])
except:
   print("Probably no tor...")
   
def waitKey():
   if not os.path.exists("data/hs_ed25519_public_key") or not os.path.exists("data/hs_ed25519_secret_key"):
      time.sleep(0.1)
      waitKey()
waitKey()

# TODO: pin persistent in memory, to be fixed
pin = None

rt = RequestsTor(tor_ports=[config["torPort"]])

with open("data/hostname", "r") as f: 
   onion = f.read()[:-7] # :-7 => .onion

# derives key from user pin 
# TODO: fixed salt, to be fixed

def get_key(pin):
    pin_bytes = str(pin).encode('utf-8')
    salt = b'MyFixedSalt' 
    derived_key = PBKDF2(pin_bytes, salt, iterations=100000).read(32)
    return derived_key

def write_chat(filename, content, pin):
   nonce = nacl.utils.random(24)
   box = SecretBox(get_key(pin))
   encrypted_message = box.encrypt(content.encode('utf-8'), nonce)
   with open(filename, "wb") as f:
       f.write(encrypted_message)

def read_chat(filename, pin, is_file = False):
   box = SecretBox(get_key(pin))
   with open(filename, "rb") as f:
       content = f.read()
   decrypted_message = box.decrypt(content)
   if not is_file:
      return decrypted_message.decode('utf-8')

# Generates a rolling secret, see server(/receive) route
def set_otp(onion):
   with open(f"data/codes/{onion}.txt", "w") as f:
      f.write(secrets.token_hex(32))

# Short hand for the secret, 
def read_otp(onion):
   with open(f"data/codes/{onion}.txt", "r") as f:
      return f.read()

# duress code implementation, see /auth route
def duress(folder_path):
   for filename in os.listdir(folder_path):
      file_path = os.path.join(folder_path, filename)
      if os.path.isfile(file_path):
         os.remove(file_path)

# generates enc keys
if not os.path.exists("data/crypt/curve_pub.key") or not os.path.exists("data/crypt/curve_priv.key"):
   os.makedirs("data/crypt", exist_ok=True) 
   private_key = PrivateKey.generate()
   public_key = private_key.public_key
   priv_bytes = private_key.encode()
   pub_bytes = public_key.encode()
   with open("data/crypt/curve_priv.key", "wb") as f:
      f.write(priv_bytes)
   with open("data/crypt/curve_pub.key", "wb") as f:
      f.write(pub_bytes)

with open("data/crypt/curve_pub.key", "rb") as f:
   tor_pub_key = f.read()

# encrypt and decrypt message functions
def encrypt_message(message, peer_public_key_bytes):
    peer_pub = PublicKey(peer_public_key_bytes)
    box = SealedBox(peer_pub)
    encrypted = box.encrypt(message.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

def decrypt_message(encrypted_message_b64):
    encrypted = base64.b64decode(encrypted_message_b64)
    with open("data/crypt/curve_priv.key", "rb") as f:
        priv = PrivateKey(f.read())
    box = SealedBox(priv)
    decrypted = box.decrypt(encrypted)
    return decrypted.decode("utf-8")
 
# TODO: Add some kind of USBkill implementation

# Client side displayed in embedded browser => app flask server

app = Flask(__name__)
@app.route("/")
def send_main():
    if shutil.which(config["tor"]) is None:
       return send_from_directory("app", "notor.html") # no tor == No chat
    if os.path.exists("data/confirm"):
      return send_from_directory("app", "index.html")
    else:
      return send_from_directory("app", "introduction.html") # first use

# For ui purposes, no XSS since app is internal only
@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('app', filename)

@app.route('/submit-pin', methods=["POST"])
def get_pin():
   if not os.path.exists("data/confirm"):
      # confirm file encrypted with pin generated key, see /auth
      write_chat("data/confirm", "test_phrase", request.form["pin"])
      return redirect("/index.html")

@app.route("/auth", methods=["POST"])
def confirm_auth():
   try:
      read_chat("data/confirm", request.form["pin"])
      global pin
      pin = request.form["pin"]
      return '<div hx-trigger="load" hx-get="/chats.html" hx-target="body"></div>'
   except:
      try:
         # If pin is 1234, and the user inputs the opposite, so 4321
         # the program on fail will reverse the reversed pin, and if it works
         # it will delete all the rest of the files
         read_chat("data/confirm", request.form["pin"][::-1])

         duress("data/chats")
         duress("data/codes")
         
         pin = request.form["pin"][::-1]
         return '<div hx-trigger="load" hx-get="/chats.html" hx-target="body"></div>'
      except:
         return "<p>Oops, looks like the wrong pin!</p>"
   
old_contacts = None
@app.route("/chats/<name>", methods=["GET", "POST"])
def send_chats(name):
   if name == "contacts":
      global old_contacts
      directory_path = "data/chats"
      files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
      if files:
         html_string = ""
         for file_name in files:
            file_name_without_extension = os.path.splitext(file_name)[0]
            href = f"/chats/{file_name_without_extension}"
            html_string += f"<p><a hx-get='{href}' hx-target='#chat'>{file_name_without_extension}</a></p>"
      else:
         html_string = "Nothing here!"

      if html_string == old_contacts:
         abort(500)
      old_contacts = html_string
      return html_string
   
   elif name == "create":
      write_chat("data/chats/" + request.form["hash"] + ".html", """<main></main>""", pin)

   # New chat context
   elif name == "new":
      return """<p>New Chat</p>
                <p>Insert the hash of whom you want to visit (without the .onion)</p>
                <form hx-post="/chats/create" hx-trigger="submit" hx-target="body">
                    <input type="text" placeholder="Enter the hash here..." name="hash" />
                    <input type="submit" value="Submit" />
                </form>
                <div hx-get="/reset_read" hx-trigger="load" hx-swap="none"></div>"""

   # Chatbox context
   else:
      return f"""<div id="header"><p>{name}</p></div>
                 <div hx-get="/read/{name}" hx-trigger="load, every 1s" hx-swap="innerHTML focus-scroll:true"></div>
                 <form hx-post="/send/{name}" hx-trigger="submit" hx-swap="none" id="inputbox">
                    <input type="text" placeholder="Enter your message here..." name="message"/>
                    <input type="submit" value="Submit" />
                    <input type="file" id="fileInput" name="file" hx-post="/sendfile/{name}" hx-encoding="multipart/form-data" hx-trigger="change" 
                hx-swap="none">
                </form>"""

last_request = ""

@app.route("/read/<name>")
def read_only_chats(name):
   global last_request
   if read_chat("data/chats/" + name + ".html", pin) != last_request:
      last_request = read_chat("data/chats/" + name + ".html", pin)
      return read_chat("data/chats/" + name + ".html", pin)
   else:
      abort(500)

@app.route("/reset_read")
def reset_read():
   global last_request
   last_request = ""
   return "OK!"

@app.route("/send/<name>", methods=["POST"])
def send_message(name):
   if not os.path.exists(f"data/codes/{name}.txt"):
      set_otp(name)
   content = read_chat("data/chats/" + name + ".html", pin)
   write_chat("data/chats/" + name + ".html", content.replace("<main>", '<main><p id="you">{}</p>'.format(request.form["message"])),  pin)
   target_url = "http://"+ name + ".onion"
   pubkey = rt.get(target_url + "/key").content

   encrypted_message = encrypt_message(
      request.form["message"],
      pubkey
   )
   
   json_data = {
      'message': encrypted_message,
      # See /receive_message
      'onion_address': onion,
      'otp': read_otp(name)
   }
   headers = {
    'Content-Type': 'application/json',
   }
   try:
      rt.post(target_url, json=json_data, headers=headers)

   except requests.exceptions.RequestException as e:
      print(f"Error: {e}")
   
   return "OK!"


@app.route("/sendfile/<name>", methods=["POST"])
def send_file(name):
   target_url = "http://"+ name + ".onion"
   pubkey = rt.get(target_url + "/key").content
   file = request.files["file"]
   mimetype = mimetypes.guess_type(file.filename)
   base64_data = base64.b64encode(file.read()).decode('utf-8')
   message = f"FILE: <a download='{file.filename}' href='data:{mimetype};base64,{base64_data}'>{file.filename}</a>"
   encrypted_message = encrypt_message(
      message,
      pubkey
   )
   requests.post(request.url_root + "/send/" + name, data={"message": encrypted_message, 'onion_address': onion, 'otp': read_otp(name)})
   return "OK!"

@app.route("/your_hash")
def send_hash():
   with open("data/hostname", "r") as f:
      return f"<p>{f.read()[:-7]}</p>"
   
# Public requests available on .onion => server flask server

server = Flask(__name__)

@server.route("/", methods=["POST"])
def receive_message():
   data = request.get_json()
   message = decrypt_message(data["message"])
   """Remote Duress
   If NoSnoop is being taken over by threat actor impersonating you,
   duress() will nuke not only chats/ and codes/ but also encryption and decryption keys
   effectively deleting the .onion service"""
   if message == pin[::-1]:
      duress("data/")
   address = "data/chats/{}.html".format(data["onion_address"])
   json_data = {
      'is': data["otp"]
   }
   headers = {
    'Content-Type': 'application/json',
   }
   
   """OTP Verification
   Instead of verifying the .onion address from the POST request directly,
   NoSnoop uses OTP based verification. 
   
   When a request is sent using /send, an onion_address and a otp parameters are sent.
   On the server(/receive_message) he doesn't trust the onion_address automatically,
   but instead checks for the OTP value on the {onion_address}.onion/check route.
   The /check route returns a 200 if the OTP value sent by the sender is the one stored
   on the server. Otherwise, it returns a 400.
   
   NoSnoop stores a different OTP for each chat. The OTP generated by the set_otp() function
   is a 32 hex bytestring, making bruteforce impractical over the TOR network.
   """
   
   response = rt.post("http://" + data["onion_address"] + ".onion/check/" + onion, json = json_data, headers = headers)
   if not response.status_code == 200:
      abort(403)
      
   if os.path.exists(address):
      if "message" in data:
         chat_content = read_chat(address, pin)
         write_chat(address, chat_content.replace("<main>", f'<main><p id="other">{bleach.clean(message, tags=["a", "i", "b"], attributes={"a": ["download", "href"]}, protocols=["data"])}</p>'), pin)
   else:
      if "message" in data:
         write_chat(address, f"""<main><p id="other">{bleach.clean(data["message"], tags=["a", "i", "b"], attributes={"a": ["download", "href"]}, protocols=["data"])}</p></main>""", pin)
   return "OK" # 👍

@server.route("/key")
def send_key():
   return Response(tor_pub_key, mimetype='application/octet-stream')

@server.route("/check/<name>", methods=["POST"])
def check_otp(name):
   data = request.json
   if data["is"] == read_otp(name):
      set_otp(name)
      return "cool!"
   else:
      abort(400)

ui = FlaskUI(app=app, server="flask", height=600, width=1400, browser_path=config["browser"])

def run_flask_ui():
    ui.run()

def run_server():
    server.run(port=config["receivePort"])

if __name__ == "__main__":
    if shutil.which(config["browser"]) is not None:
      config["browser"] = None
    thread_flask_ui = threading.Thread(target=run_flask_ui)
    thread_server = threading.Thread(target=run_server)
    thread_flask_ui.start()
    thread_server.start()
    thread_flask_ui.join()
    thread_server.join()