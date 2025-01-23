import subprocess
import time
from threading import Thread
import socket
import os
import base64


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
print("ROOT_DIR", ROOT_DIR)


def open_browser(html_file, browser=None, browser_args=[]):
    if(browser != None and "selenium" in browser):
        from selenium import webdriver
        if("chrome" in browser):
            options = webdriver.ChromeOptions()
            options.add_argument('--ignore-certificate-errors')
            options.add_argument("--test-type")
            for x in browser_args:
                if(x):
                    options.add_argument(x)
            driver = webdriver.Chrome(options=options)
            driver.get(html_file)
        elif("firefox" in browser):

            #             geckodriver = 'C:\\Users\\grayson\\Downloads\\geckodriver.exe'

            # browser =
            options = webdriver.FirefoxOptions()
            # options.add_argument('--ignore-certificate-errors')
            # options.add_argument("--test-type")
            for x in browser_args:
                if(x):
                    options.add_argument(x)
            driver = webdriver.Firefox(options=options)
            driver.get(html_file)
        else:
            raise ValueError("Browser %r not supported" % browser)
    elif(browser != None and browser != "none"):
        browser_process = subprocess.Popen(
            [browser, html_file] + browser_args)
    elif(browser != "none"):
        # use defualt browser
        import webbrowser
        webbrowser.get().open(html_file)

from flask import Flask, request, jsonify, send_from_directory
import json
import os

# -----------------------------------------------------------
# : Flask Server Endpoints 

app = Flask(__name__)

@app.route('/get_next_html', methods=['GET'])
def get_next_html():
    print("GET NEXT HTML")
    try:
        return 'http://localhost:3000/Mathtutor/6_01_HTML/HTML/6.01-4.html'
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/save_html_json', methods=['POST'])
def save_html_json():
    print("SAVE HTML JSON")
    try:
        # Get JSON data from request
        data = request.get_json()
                
                
        return jsonify({"status": "success", "message": "JSON data saved successfully"}), 200
    
    except Exception as e:

        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/save_html_image', methods=['POST'])
def save_html_image():
    print("SAVE HTML IMAGE")
    try:
        # Get JSON data from request
        data = request.get_json()
        print(data)
        # Decode the base64 image
        image_data = data['image'].replace("data:image/png;base64,", "")
        # image_data = data['image'].replace(" ", "+")
        image_data = base64.b64decode(image_data)

        print(image_data)

        with open("my_image.png", 'wb') as f:
            f.write(image_data)
        
        return jsonify({"status": "success", "message": "Image saved successfully"}), 200
    
    except Exception as e:
        print(request)
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 400


# Also serve root index.html
@app.route('/<path:filename>')
def serve_static(filename):
    print("--serve_static:", filename)
    return send_from_directory(ROOT_DIR, filename)

# -----------------------------------------------------------
# : Start Flask Server 

def is_server_running(host='localhost', port=3000):
    """Check if the server is running by attempting to connect to it"""
    try:
        socket.create_connection((host, port), timeout=1)
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def start_flask_server():
    def run_flask():
        app.run(host='localhost', port=3000)

    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Wait for the server to start
    print("Waiting for Flask server to start...")
    while not is_server_running():
        time.sleep(0.1)  # Check every 100ms
    print("Flask server is now running!")

if __name__ == '__main__':
    start_flask_server()
    # browser_process = open_browser("Mathtutor/6_01_HTML/HTML/6.01-4.html", "google-chrome")
    browser_process = open_browser("http://localhost:3000/index.html", "firefox")

    while is_server_running():
        time.sleep(0.1)  # Check every 100ms
    

