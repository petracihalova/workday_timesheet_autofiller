# Workday timesheet autofiller

Tool to fill the Workday timesheet due by the end of the month.

No big magic, Selenium + Python + Chrome webdriver find all weeks that are fillable and fill in hours using template saved in the `.env` file (`TEMPLATE`). 

The days that already contain some record (hours != 0) are skipped. Weekend days are skipped too. If your template contains two time blocks, the "Meal" is added as the "Out reason" between them. There is simple validation of `TEMPLATE` but it is not checked if hours sum is 8.

## How to use
Clone the repo
* `git clone git@github.com:petracihalova/workday_timesheet_autofiller.git`


Go into project folder and create + activate new virtual environment
* `cd workday_timesheet_autofiller`
* `python3 -m venv venv`
* `source venv/bin/activate`


Install dependencies
* `pip install -r requirements.txt`


Create new .env file
* `cp .env.example .env`


In the .env config set `TEMPLATE` and `LOGIN` values


Run app
* `python start.py`
