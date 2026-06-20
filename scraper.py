import requests
import json
import bs4


def fetch():

    url = "https://api.easi.utoronto.ca/ttb/getPageableCourses"
    payload_raw = """{"courseCodeAndTitleProps":{"courseCode":"","courseTitle":"","courseSectionCode":""},"departmentProps":[],"campuses":[],"sessions":["20269","20271","20269-20271"],"requirementProps":[],"instructor":"","courseLevels":[],"deliveryModes":[],"dayPreferences":[],"timePreferences":[],"divisions":["ARTSC"],"creditWeights":[],"availableSpace":false,"waitListable":false,"page":1,"pageSize":20,"direction":"asc"}"""
    payload = json.loads(payload_raw)

    req = requests.post(url, json=payload)

    soup = bs4.BeautifulSoup(req.content, "html.parser")

    return soup






