import requests
from typing import Union
from pytrends.request import TrendReq
from fastapi import FastAPI, Query
import json
from typing import List
import pandas as pd
from datetime import date, datetime, timedelta
import time

app = FastAPI()


def get_trends_with_retry(keyword, start_date, end_date):
    end_time = datetime.now() + timedelta(minutes=3)
    pytrends = TrendReq(hl="en-US", tz=360)
    should_retry = True

    while datetime.now() < end_time and should_retry:
        try:
            # Format the dates for the payload
            timeframe = (
                f"{start_date.strftime('%Y-%m-%d')} {end_date.strftime('%Y-%m-%d')}"
                if start_date and end_date
                else "today 12-m"
            )
            pytrends.build_payload([keyword], timeframe=timeframe)
            data = pytrends.interest_over_time()

            if not data.empty and "isPartial" in data.columns:
                data = data.drop(columns=["isPartial"])
                data = data.reset_index()
                result = data.to_json(orient="records", date_format="iso")
                result_data = json.loads(result)
                return {"status": 200, "data": result_data}

        except Exception as e:
            print(f"An error occurred: {e}")
            message = f"{e}"
            if "Google returned a response with code 429" not in message:
                should_retry = False
                print("different error?")
                return {"status": 500, "message": f"{e}"}

        # Sleep for a short duration to avoid hitting the rate limit too quickly
        time.sleep(10)

    return None


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/trends/{keyword}")
def get_trends(keyword, start_date: date = Query(None), end_date: date = Query(None)):
    try:
        data = get_trends_with_retry(keyword, start_date=start_date, end_date=end_date)
        return data

    except Exception as error:
        return {"status": 500, "message": "{}".format(error)}
