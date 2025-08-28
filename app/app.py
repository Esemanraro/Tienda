# app/app.py
from . import create_app
app = create_app()

if __name__ == "__main__":
    app.run(host="192.168.0.51", port=5070)
