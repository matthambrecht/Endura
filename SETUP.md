# Endura - Setup
1. Run `python3 -m venv venv` in your project directory to build the virtual enviroment and avoid dependency issues.
2. Depending on your system run the following commands
    a. Windows: `.\venv\Scripts\activate`
    b. Linux: `. venv/bin/activate`
3. Run `pip3 install -r requirements.txt` to get the requirements for the api.
4. Start the API with `uvicorn app:app --workers=6 --port 3000 --log-config=log_conf.yaml --reload` in the `api` directory.
5. To ensure the api is up and running properly open `health.html` and hit the "Get Health" button. You can kill the api with CTRL+C.