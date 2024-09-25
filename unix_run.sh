#!/bin/bash
if [ ! -d "venv" ]; then
    python3 -m venv venv
    . venv/bin/activate
    pip3 install -r requirements.txt
fi

. venv/bin/activate
python3 app/app.py
