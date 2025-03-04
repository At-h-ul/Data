import os
from fastapi import FastAPI, Query
from tasks import scrape_gp

app = FastAPI()

@app.post("/scrape/")
def scrape(url: str = Query(...)):
    csv_file_path = os.path.join(os.path.dirname(__file__), "data", "scraped_villages.csv")
    scrape_gp.send(url, 0, 0, 0, 0, csv_file_path)
    return {"message": "Scraping started"}