import subprocess
import time
from threading import Thread, Lock
import socket
import os
import sys
import base64
import glob
import warnings
from tutorgym.shared import glob_iter
from queue import Queue



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
from flask_socketio import SocketIO, send, emit
import json
import os

# -----------------------------------------------------------
# : Flask Server Endpoints 

# class MessageSender:
#     def __init__(self, message_queue, emit_func):
#         self.running = True
#         self.message_queue = message_queue
#         self.emit_func = emit_func
    
#     def stop(self):
#         self.running = False

#     def run(self):
#         while self.running:
#             try:
#                 # Process messages from queue
#                 while not self.message_queue.empty():
#                     msg = self.message_queue.get()
#                     emit_func('html_configs', msg)
                
#                 # # Send periodic updates
#                 # socketio.emit('heartbeat', {'timestamp': time.time()})
#                 # time.sleep(1)
                
#             except Exception as e:
#                 print(f"Error in message sender: {str(e)}")
#                 time.sleep(1)

def build_flask_server(host, port, root_dir):
    # message_queue = Queue()
    app = Flask("html_tools_server")
    socketio = SocketIO(app)
    host_url = f"http://{host}:{port}"
    flask_thread = None
    message_thread = None
    # message_sender = MessageSender(message_queue, socketio.emit)
    html_configs = []

    connect_lock = Lock()
    connect_lock.acquire()


    # config_index = 0

    # @app.route('/get_html_configs', methods=['GET'])
    # def get_html_configs():
    #     print("GET HTML CONFIGS")
    #     try:
    #         return jsonify(html_configs) #f'{host_url}/Mathtutor/6_01_HTML/HTML/6.01-4.html'
        
    #     except Exception as e:
    #         return jsonify({"status": "error", "message": str(e)}), 400

    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        connect_lock.release()

    @socketio.on('disconnect')
    def handle_connect():
        print('Client disconnected')
        connect_lock.acquire()

    @app.route('/save_html_json', methods=['POST'])
    def save_html_json():
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

    @app.route('/processing_finished', methods=['POST'])
    def processing_finished():
        print("Processing Finished.")
        shutdown_func = request.environ.get('werkzeug.server.shutdown')
        if shutdown_func is not None:
            shutdown_func()
        else:
            import signal
            os.kill(os.getpid(), signal.SIGINT)
            
            # cleanup()
            # signal.raise_signal(signal.SIGABRT)
            # print("SYS EXIT")
            # pid = os.getpid()
            # # Send SIGTERM signal to the process
            # os.kill(pid, signal.SIGTERM)
            # sys.exit(0)
        return jsonify({"message" : "Server shutting down..."}) #f'{host_url}/Mathtutor/6_01_HTML/HTML/6.01-4.html'
        

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




    def run_flask():
        socketio.run(app, host=host, port=port)

    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True # cleanup when main process does
    flask_thread.start()

    return flask_thread, socketio.emit, connect_lock

# -----------------------------------------------------------
# : Start Flask Server 

def is_server_running(host='localhost', port=3000):
    """Check if the server is running by attempting to connect to it"""
    try:
        socket.create_connection((host, port), timeout=1)
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False

# def start_flask_server(host, port, root_dir):
#     # emit_queue = Queue()
#     flask_thread, emit_func = build_flask_server(host, port, root_dir)
#     return flask_thread, emit_func#, emit_queue


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


def get_cached_proc_filepath(root_dir, html_path, long_hash=None, new_ext='.json'):
    if(long_hash is None):
        long_hash = get_file_longhash(os.path.join(root_dir, html_path))
    directory, name, ext = split_filepath(html_path)
    return f"{directory}/.{name}.tgym_{long_hash[:14]}{new_ext}"




# -----------------------------------------------------------
# : HTML_Preprocessor 


class HTML_Preprocessor:
    def __init__(self, root_dir, 
                 get_json=True, get_image=True, 
                 cache=True, 
                 browser="firefox", browser_args=[],
                 host='localhost', port=3000):

        self.root_dir = root_dir
        self.get_json = get_json
        self.get_image = get_image
        self.cache = cache
        self.browser = browser
        self.browser_args = browser_args
        self.host = host
        self.port = port


        # self.is_done = False

    def _process_paths(self, html_paths):
        if(isinstance(html_paths, (str,dict))):
            html_paths = [html_paths]

        processed_html_configs = [] 
        for i, html_path in enumerate(html_paths):
            if(isinstance(html_path, str)):
                config = {}
                config['html_path'] = html_path
            elif(isinstance(html_path, dict)):
                config = html_path

            config['get_json'] = config.get('get_json', self.get_json)
            config['get_image'] = config.get('get_image', self.get_json)
            config['cache'] = config.get('cache', self.cache)

            valid_config = False
            if("html_path" in config):
                if("*" in html_path):
                    config['glob'] = {"pathname": html_path, "root_dir": self.root_dir,  "recursive" : True}
                    del config['html_path']
                else:
                    valid_config = True
                    processed_html_configs.append(config)
        
            if("glob" in config):
                item_config = {k:v for k,v in config.items() if k != "glob"}


                for html_path in glob_iter(**config["glob"]):
                    if(not html_path.endswith(".html")):
                        warnings.warn(f"HTML path ({html_path}) retrieved by glob arguments {config['glob']} does not end in '.html'.")

                    processed_html_configs.append({"html_path" : html_path, **item_config})
                valid_config = True

            if(not valid_config):
                raise ValueError(f"Invalid config {config}. Must have valid 'html_path' or 'glob' key.")

        html_configs, need_run_browser = self._ensure_outpaths(processed_html_configs)
        return html_configs, need_run_browser

    def _ensure_outpaths(self, html_configs): 
        need_run_browser = False

        for html_config in html_configs:
            get_json = html_config.get('get_json', True)
            get_image = html_config.get('get_json', True)
            if(not get_json and not get_image):
                continue 

            # print("html_path", html_config['html_path'])

            html_path = html_config['html_path']
            abs_html_path = os.path.join(self.root_dir, html_path) 
            longhash = get_file_longhash(abs_html_path)

            # Ensure that 'json_path' and 'image_path' exist
            if(get_json and not 'json_path' in html_config):
                html_config['json_path'] = \
                    get_cached_proc_filepath(self.root_dir, html_path, longhash, '.json')

            if(get_image and not 'image_path' in html_config):
                html_config['image_path'] = \
                    get_cached_proc_filepath(self.root_dir, html_path, longhash, '.png')

            # When cache=True don't overwrite  
            cache = html_config.get('cache', True)
            # json_path = os.path.join(self.root_dir, html_config['json_path'])
            json_path = html_config['json_path']
            # print("json_path", json_path)
            if(cache and os.path.exists(json_path)):
                html_config['get_json'] = False
            else:
                need_run_browser = True

            image_path = html_config['image_path']
            # image_path = os.path.join(self.root_dir, html_config['image_path'])
            # print("image_path", image_path)
            if(cache and os.path.exists(image_path)):
                html_config['get_image'] = False
            else:
                need_run_browser = True

        # self.need_run_browser = need_run_browser
        return html_configs, need_run_browser

    def _ensure_browser(self):
        if(not hasattr(self, 'flask_thread')):
            self.flask_thread, self.emit, self.connect_lock = build_flask_server(self.host, self.port, self.root_dir)
            host_url = f"http://{self.host}:{self.port}"
            self.browser_process = open_browser(f"{host_url}/html_tools/index.html", self.browser)

            self.emit_queue = Queue()

            def handle_emit_queue():
                while True:
                    with self.connect_lock:
                        html_configs, emit_lock = self.emit_queue.get()

                        def send_html_configs_callback(data):
                            emit_lock.release()

                        print(" -- DO EMIT -- ")
                        self.emit("send_html_configs", 
                         {"html_configs" : html_configs}, 
                         callback=send_html_configs_callback)

                        # Don't continue until the client returns has finished 
                        #  processing all of the html files
                        with emit_lock:
                            print(" -- EMIT FINISHED -- ")
                            pass

            self.emit_thread = Thread(target=handle_emit_queue)
            self.emit_thread.daemon = True # cleanup when main process does
            self.emit_thread.start()

    # def send_html_configs_callback(self, data):
    #     self.emit_queue.put(data)

    def process_htmls(self, html_paths, block=True, keep_alive=True, **kwargs):
        html_configs, need_run_browser = self._process_paths(html_paths)

        if(need_run_browser):
            self._ensure_browser()
        
        emit_lock = Lock()
        emit_lock.acquire()
        self.emit_queue.put((html_configs, emit_lock))

        if(block):
            print("-- BEFORE LOCK --")
            with emit_lock:
                pass
            print("-- AFTER LOCK --")
            return html_configs
        else:
            return html_configs, emit_lock

    # def get_configs(self):
    #     return self.html_configs

    def shutdown(self):
        flask_thread = getattr(self, "flask_thread", None)
        if(flask_thread is not None):
            os.kill(flask_thread.native_id, signal.SIGINT)


    def __del__(self):
        self.shutdown()


if __name__ == '__main__':
    # start_flask_server()
    # # browser_process = open_browser("Mathtutor/6_01_HTML/HTML/6.01-4.html", "google-chrome")
    # browser_process = open_browser("http://localhost:3000/index.html", "firefox")
    html_proc = HTML_Preprocessor(
        root_dir="../envs/CTAT/Mathtutor/",
    )

    html_configs, lock1 = html_proc.process_htmls(html_paths="**/*.html", block=False)
    html_configs, lock2 = html_proc.process_htmls(html_paths="**/*.html", block=False)

    with lock1:
        print("-- FINISH 1 --")

    with lock2:
        print("-- FINISH 2 --")


    # print("START")

    # proc.start()

    # print("END")
    # proc.get

    for config in html_configs:
        print(config)

    # while is_server_running():
    #     time.sleep(0.1)  # Check every 100ms
    

