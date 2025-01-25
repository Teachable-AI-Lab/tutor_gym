import subprocess
import time
from threading import Thread
import socket
import os
import base64
import glob
import warnings


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
# print("ROOT_DIR", ROOT_DIR)


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

def build_flask_server(host, port, root_dir, html_configs):
    app = Flask("html_tools_server")
    host_url = f"http://{host}:{port}"
    # config_index = 0

    @app.route('/get_html_configs', methods=['GET'])
    def get_html_configs():
        print("GET HTML CONFIGS")
        try:
            # html_config = html_configs[config_index]
            # html_config['config_index'] = config_index
            # config_index += 1

            # html_config['html_url'] = host_url + html_config['html_path']


            return jsonify(html_configs) #f'{host_url}/Mathtutor/6_01_HTML/HTML/6.01-4.html'
        
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400


    @app.route('/save_html_json', methods=['POST'])
    def save_html_json():
        print("SAVE HTML JSON")
        try:
            # Get JSON data from request
            data = request.get_json()
            
            filepath = os.path.join(root_dir, data['filepath'])

            with open(filepath, 'w') as f:
                json.dump(data['html_json'], f)

                    
            return jsonify({"status": "success", "message": "JSON data saved successfully"}), 200
        
        except Exception as e:
            print(e)
            return jsonify({"status": "error", "message": str(e)}), 400

    @app.route('/save_html_image', methods=['POST'])
    def save_html_image():
        print("SAVE HTML IMAGE")
        try:
            # Get JSON data from request
            data = request.get_json()
            # Decode the base64 image
            image_data = data['image_data'].replace("data:image/png;base64,", "")
            # image_data = data['image'].replace(" ", "+")
            image_data = base64.b64decode(image_data)
            filepath = os.path.join(root_dir,data['filepath'])

            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            return jsonify({"status": "success", "message": "Image saved successfully"}), 200
        
        except Exception as e:
            print(e)
            return jsonify({"status": "error", "message": str(e)}), 400


    # Also serve root index.html
    @app.route('/<path:filename>')
    def serve_static(filename):
        print(f"--serve_static: /{filename}")
        return send_from_directory(root_dir, filename)

    # Also serve root index.html
    @app.route('/html_tools/<filename>')
    def serve_html_tools(filename):
        print(f"--serve_static: /html_tools/", filename)
        return send_from_directory(THIS_DIR, filename)


    return app

# -----------------------------------------------------------
# : Start Flask Server 

def is_server_running(host='localhost', port=3000):
    """Check if the server is running by attempting to connect to it"""
    try:
        socket.create_connection((host, port), timeout=1)
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def start_flask_server(host, port, root_dir, html_configs):
    app = build_flask_server(host, port, root_dir, html_configs)
    def run_flask():
        app.run(host=host, port=port)

    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Wait for the server to start
    print("Waiting for Flask server to start...")
    while not is_server_running():
        time.sleep(0.1)  # Check every 100ms
    print("Flask server is now running!")
    return flask_thread


# -----------------------------------------------------------
# : Cache'd file naming 

import hashlib

def split_filepath(filepath):
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)
    
    return directory, name, ext

def get_file_longhash(filename):
    """Calculates the SHA-256 hash of a file."""

    hasher = hashlib.sha256()
    with open(filename, 'rb') as file:
        while True:
            chunk = file.read(4096)  # Read file in chunks
            if not chunk:
                break
            hasher.update(chunk)

    b64str = base64.b64encode(hasher.digest(), altchars=b'AB').decode('utf-8')
    return b64str


def get_cached_proc_filepath(html_path, long_hash=None, new_ext='.json'):
    if(long_hash is None):
        long_hash = get_file_longhash(html_path)
    directory, name, ext = split_filepath(html_path)
    return f"{directory}/.{name}.tgym_{long_hash[:14]}{new_ext}"




# -----------------------------------------------------------
# : HTML_Preprocessor 

class HTML_Preprocessor:
    def __init__(self, root_dir, html_paths, 
                 get_json=True, get_image=True, 
                 disk_cache=True, 
                 browser="firefox", browser_args=[],
                 host='localhost', port=3000):
        if(isinstance(html_paths, (str,dict))):
            html_paths = [html_paths]

        processed_html_configs = [] 
        for i, html_path in enumerate(html_paths):
            if(isinstance(html_path, str)):
                config = {}
                config['html_path'] = html_path
            elif(isinstance(html_path, dict)):
                config = html_path

            config['get_json'] = config.get('get_json', get_json)
            config['get_image'] = config.get('get_image', get_json)
            # config['disk_cache'] = config.get('disk_cache', disk_cache)

            valid_config = False
            if("html_path" in config):
                if("*" in html_path):
                    print(os.path.join(root_dir, html_path))
                    config['glob'] = {"pathname": html_path, "root_dir":root_dir,  "recursive" : True}
                    del config['html_path']
                else:
                    valid_config = True
                    processed_html_configs.append(config)
        
            if("glob" in config):
                item_config = {k:v for k,v in config.items() if k != "glob"}
                for html_path in glob.glob(**config["glob"]):
                    if(not html_path.endswith(".html")):
                        warnings.warn(f"HTML path ({html_path}) retrieved by glob arguments {config['glob']} does not end in '.html'.")

                    processed_html_configs.append({"html_path" : html_path, **item_config})
                valid_config = True

            if(not valid_config):
                raise ValueError(f"Invalid config {config}. Must have valid 'html_path' or 'glob' key.")

        self.root_dir = os.path.abspath(root_dir)
        self.html_configs = processed_html_configs
        self.browser = browser
        self.browser_args = browser_args
        self.host = host
        self.port = port
        self.is_done = False

        self.ensure_outpaths(disk_cache)

    def ensure_outpaths(self, disk_cache): 
        for html_config in self.html_configs:
            get_json = html_config.get('get_json', True)
            get_image = html_config.get('get_json', True)
            if(not get_json and not get_image):
                continue 

            html_path = html_config['html_path']
            longhash = get_file_longhash(os.path.join(self.root_dir, html_path))

            # Ensure that 'json_path' and 'image_path' exist
            if(get_json and not 'json_path' in html_config):
                html_config['json_path'] = \
                    get_cached_proc_filepath(html_path, longhash, '.json')

            if(get_image and not 'image_path' in html_config):
                html_config['image_path'] = \
                    get_cached_proc_filepath(html_path, longhash, '.png')

            # When disk_cache=True don't overwrite  
            if(disk_cache and os.path.exists(html_config['json_path'])):
                html_config['get_json'] = False

            if(disk_cache and os.path.exists(html_config['image_path'])):
                html_config['get_image'] = False


    def start(self, block=True):
        self.flask_thread = start_flask_server(self.host, self.port, self.root_dir, self.html_configs)

        host_url = f"http://{self.host}:{self.port}"
        # host_url = html_paths
        browser_process = open_browser(f"{host_url}/html_tools/index.html", "firefox")

        while is_server_running(self.host, self.port):
            time.sleep(0.1)  # Check every 100ms


    def get_configs(self):
        return self.html_configs





            

            




if __name__ == '__main__':
    # start_flask_server()
    # # browser_process = open_browser("Mathtutor/6_01_HTML/HTML/6.01-4.html", "google-chrome")
    # browser_process = open_browser("http://localhost:3000/index.html", "firefox")
    proc = HTML_Preprocessor(
        root_dir="../../envs/CTAT/Mathtutor/",
        html_paths="**/*.html"
    )

    proc.start()

    # for config in proc.get_configs():
    #     print(config)

    # while is_server_running():
    #     time.sleep(0.1)  # Check every 100ms
    

