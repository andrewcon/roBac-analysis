from bs4 import BeautifulSoup
from time import sleep
from tqdm.auto import trange
from unidecode import unidecode
from fake_useragent import UserAgent
import json, requests

ua = UserAgent(cache=False)

#Define what will ultimately become the list with all the data
mydata = []

for x in trange(1, 42, desc='Total progress'):
    #Load first page of county
    #Notice that the county id and page id are inside the url
    url = f'http://evaluare.edu.ro/Evaluare/CandFromJudAlfa.aspx?Jud={x}&PageN=1'
    r = requests.get(url, headers={'User-Agent': ua.random})

    #Use soup to get page content
    soup = BeautifulSoup(r.content, 'html.parser')

    #Get name of current county and assign it in lower-case
    county_name = soup.select_one('#ContentPlaceHolderBody_LabelTitle').text.strip().lower().split()[-1]

    #Get number of pages for current county
    pagenum = soup.select('select option', {"id":"ContentPlaceHolderBody_DropDownList2"})
    pagenum = int(pagenum[-1]['value'])

    for y in trange(1, pagenum + 1, desc='Current county progress', leave=False):
        if y > 1:
            url = f'http://evaluare.edu.ro/Evaluare/CandFromJudAlfa.aspx?Jud={x}&PageN={y}'
            r = requests.get(url, headers={'User-Agent': ua.random})
            soup = BeautifulSoup(r.content, 'html.parser')
        else: pass

        rows = soup.select('#ContentPlaceHolderBody_FinalDiv tr')

        #Iterate through each row in the table of the current page
        for row in rows[2:]:
            d = dict()

            d['judet'] = county_name
            d['cod'] = row.find_all('td')[1].text.strip()
            d['scoala'] = unidecode(row.find_all('td')[3].text.strip().lower())
            d['romana_nota'] = row.find_all('td')[4].text.strip()
            d['romana_contestatie'] = row.find_all('td')[5].text.strip()
            d['romana_nota_finala'] = row.find_all('td')[6].text.strip()
            d['matematica_nota'] = row.find_all('td')[7].text.strip()
            d['matematica_contestatie'] = row.find_all('td')[8].text.strip()
            d['matematica_nota_finala'] = row.find_all('td')[9].text.strip()
            d['limba_materna'] = row.find_all('td')[10].text.strip().lower()
            d['limba_materna_nota'] = row.find_all('td')[11].text.strip()
            d['limba_materna_contestatie'] = row.find_all('td')[12].text.strip()
            d['limba_materna_nota_finala'] = row.find_all('td')[13].text.strip()
            d['media_totala_curenta'] = row.find_all('td')[14].text.strip()

            mydata.append(d)

        sleep(1)

with open('evaluare_nationala.json', 'w') as f:
    json.dump(mydata, f)