import csv
import sys
import requests

if __name__ == "__main__":
    with open(sys.argv[1], newline="") as csvfile:
        linkreader = csv.DictReader(
            csvfile,
            delimiter=",",
        )
        short_urls = []
        for row in linkreader:
            response = requests.post(
                f"http://localhost:5000/shorten", json={"long_url": row["url"]}
            )
            response_json = response.json()
            try:
                short_urls.append(response_json["short_url"])
            except BaseException as e:
                print(f"long_url: '{row['url']}, response: {response_json}")
                raise e

        print(short_urls)
