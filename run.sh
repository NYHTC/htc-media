#!/bin/bash

echo "...starting virtual environment"
source venv/bin/activate

echo "...install requirements"
pip install -r requirements.txt

echo "...starting microservice"
export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run

echo ""
echo "Remember to deactivate the virtual environment after stopping the server."
