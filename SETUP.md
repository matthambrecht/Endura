# Endura - Setup
1. Run `python3 -m venv venv` in your project directory to build the virtual enviroment and avoid dependency issues.
2. Depending on your system run the following commands
    a. Windows: `.\venv\Scripts\activate`
    b. Linux: `. venv/bin/activate`
3. Run `pip3 install -r requirements.txt` to get the requirements for the api.
4. Start the API and Frontend with `python3 app.py` in the `app` directory.

## Quick Setup
On unix-based systems (Linux, MacOS) you can run the `unix_run.sh` script and it'll handle the setup for you.
On windows systems utilize the `windows_run.bat` to setup the program.