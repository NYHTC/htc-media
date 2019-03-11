#!/bin/bash

source venv/bin/activate

export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run

echo ""
echo "Remember to deactivate the virtual environment after stopping the server."
