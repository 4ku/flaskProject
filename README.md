# Installation
** Create virtualenv
python -m virtualenv env
env\Scripts\activate
pip install -r requirements.txt
** go to flask folder **
flask db init
flask db migrate -m "init"
flask upgrade
python manager.py
pybabel compile -d app/translations