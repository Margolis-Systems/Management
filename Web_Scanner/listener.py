import os
from flask import Flask, request

if __name__ == '__main__':
    app = Flask(__name__)

    @app.route('/scanner', methods=['POST', 'GET'])
    def scanner():
        import subprocess
        subprocess.call(['c:\\web_scanner\\scan.bat'])
        return {}

    app.run(debug=True)
