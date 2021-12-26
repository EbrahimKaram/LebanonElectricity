from bs4 import BeautifulSoup
import re

if __name__ == '__main__':
    page = open("Stations.html", encoding="utf8")
    soup = BeautifulSoup(page, 'html.parser')


    print("ID, Station Name")
    for e in soup.findAll("li"):
        # /\d+$/
        # \d+$
        # print(e.get('id'))
        # print(re.findall("\d+$",e.get('id'))[0])
        print(re.findall("\d+$",e.get('id'))[0],",",e.get_text())
