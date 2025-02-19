from tutorgym.html_tools.html_tools import open_browser
from tutorgym.env_classes.CTAT.CTAT_problem_set import collect_CTAT_problem_sets
import glob 
import argparse
import threading

def start_static_serve():
    import http.server
    import socketserver

    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("Serving at port", PORT)
        httpd.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Open browser')
    
    # Add arguments
    parser.add_argument('dir', help='The file to process')
    args = parser.parse_args()
    directory = args.dir

    ps = collect_CTAT_problem_sets(directory)[0]

    prob = next(iter(ps))
    print(prob)

    # start server
    server_thread = threading.Thread(target=start_static_serve)
    server_thread.start()

    # model_path 

    url = f"http://localhost:8000/{prob['html_path']}?question_file=/{prob['model_path']}"
    open_browser(url, browser='firefox')

