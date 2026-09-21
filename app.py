"""Run with python app.py"""

from ledger import create_app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=8080, debug=True)
