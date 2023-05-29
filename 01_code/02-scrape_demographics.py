from bs4 import BeautifulSoup
from unidecode import unidecode
from fake_useragent import UserAgent
from time import sleep
from tqdm import tqdm
import pandas as pd
import json, requests

#Uses wikipedia to get all settlements of Romania
#Text converted to UTF-8
ua = UserAgent(cache=False, verify_ssl=False)

#Loads wikipedia page with all counties in Romania
#Page has links to settlements for each county
wiki_url = 'https://ro.wikipedia.org/wiki/Format:Listele_localit%C4%83%C8%9Bilor_din_Rom%C3%A2nia_pe_jude%C8%9Be'

ro_counties_page = requests.get(wiki_url, headers={'User-Agent': ua.random})

rcp_soup = BeautifulSoup(ro_counties_page.content, 'html.parser')

county_links = rcp_soup.select('tbody tr p a')

mysettlements = []

print('Retrieving all settlements in Romania')
for link in tqdm(county_links, initial=1, total=42):
    county_url = 'https://ro.wikipedia.org/' + link['href']
    county_r = requests.get(county_url)
    county_soup = BeautifulSoup(county_r.content, 'html.parser')
    county_name = county_soup.select_one('.firstHeading').text.strip()
    county_name = unidecode(county_name[32:].replace(" ", "-").lower())
    settlements_tb = county_soup.select('.wikitable tr')

    for row in settlements_tb[1:]:
        settlement_dict = dict()
        settlement_dict['nume_judet'] = county_name
        settlement_dict['nume_localitate'] = unidecode(row.select_one('td:nth-of-type(1)').get_text().strip().lower())
        settlement_dict['tip_localitate'] = unidecode(row.select_one('td:nth-of-type(2)').get_text(separator=" ").strip().split()[0].lower())

        mysettlements.append(settlement_dict)

    sleep(1)

mysettlements_df = pd.DataFrame.from_dict(mysettlements)

# aic = average income county
# number unemployed county
#Note: data from 2020
aic_link = requests.get("http://statisticiromania.ro/api/Standings/GetStandings?chapter=Forta%20de%20munca%20-%20salariu%20mediu%20net&year=2020&yearFraction=-1", headers={'User-Agent': ua.random}).text
nuc_link = requests.get("http://statisticiromania.ro/api/Standings/GetStandings?chapter=Forta%20de%20munca%20-%20numar%20someri&year=2020&yearFraction=-1", headers={'User-Agent': ua.random}).text

aic_data = json.loads(aic_link)['data']
nuc_data = json.loads(nuc_link)['data']

aic_df = pd.DataFrame(aic_data)
nuc_df = pd.DataFrame(nuc_data)

combined_df = pd.merge(aic_df, nuc_df, on="county")
combined_df = combined_df.drop(combined_df.columns[[0,3]], axis=1)
combined_df.columns = ['nume_judet','salariu_mediu_net',
                       'numar_someri']

#Get population data for each county
#Note: data from 2018
pop_df = pd.read_html("https://docs.google.com/spreadsheets/u/0/d/e/2PACX-1vQ64Eit7XcuW2WexPARvFw6fYad5y-dVxk5Nc1Oog7pO4YFfFRDe77afwI8S42KpJczmnLzM3nFYjSe/pubhtml/sheet?headers=false&gid=0", encoding='utf-8', header=1)
pop_df = pop_df[0]
pop_df.iloc[:,2] = pop_df.iloc[:,2].apply(unidecode)
pop_df = pop_df.drop(pop_df.columns[0:2], axis=1)
pop_df.columns = ['nume_judet','populatie']

combined_df = pd.merge(combined_df, pop_df, on="county")
combined_df['nr_someri_per_capita'] = combined_df['populatie'] / combined_df['numar_someri']
combined_df.iloc[:,0] = combined_df.iloc[:,0].apply(str.lower)

all_df = pd.merge(combined_df, mysettlements_df, on="county")

all_df.to_json(r'settlements_all.json')