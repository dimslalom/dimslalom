#!/usr/bin/env python3
"""Save the last year of a user's GitHub contribution calendar as JSON."""
import json
import os
import sys
import urllib.request

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
contributionCalendar{weeks{contributionDays{contributionCount date}}}}}}"""


def main():
    login, out = sys.argv[1], sys.argv[2]
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"},
    )
    with urllib.request.urlopen(request) as response:
        body = json.load(response)
    weeks = body["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [{"date": day["date"], "count": day["contributionCount"]}
            for week in weeks for day in week["contributionDays"]]
    with open(out, "w") as file:
        json.dump(days, file)


if __name__ == "__main__":
    main()
