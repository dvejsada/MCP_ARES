import requests
from bs4 import BeautifulSoup
import re
from striprtf.striprtf import rtf_to_text

def get_decision(file_no):
    # Extract components of the file number
    match = re.match(r'(\d+)\s+(\w+)\s+(\d+)/(\d+)', file_no)
    if not match or "Cdo" not in file_no:
        return "Invalid case number format."
    spzn1, spzn2, spzn3, spzn4 = match.groups()

    # Construct the URL
    base_url = 'https://rozhodnuti.nsoud.cz//Judikatura/judikatura_ns.nsf/$$WebSearch1'
    query = f'[spzn1] = {spzn1} AND [spzn2]={spzn2} AND [spzn3]={spzn3} AND [spzn4]={spzn4}'
    params = {
        'SearchView': '',
        'Query': query,
        'SearchMax': '1000',
        'SearchOrder': '4',
        'Start': '0',
        'Count': '15',
        'pohled': '1'
    }

    # Fetch the search results page
    response = requests.get(base_url, params=params)
    response.encoding = 'utf-8'

    if response.status_code != 200:
        return "Failed to retrieve the webpage."

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table containing the results
    table = soup.find('table', {'id': 'tabl'})
    if not table:
        return "No decision found for the provided case number."

    # Find the row with the decision
    rows = table.find_all('tr')
    if len(rows) < 1:
        return "No decision found for the provided case number."

    # Assuming one result, we take the first data row
    row = rows[0]
    cells = row.find_all('td')

    # Extract Kategorie
    kategorie_cell = row.find('td', {'class': 'td-short category'})
    kategorie = kategorie_cell.get_text(strip=True) if kategorie_cell else ''

    # Extract Právní věta
    pravni_veta_cell = row.find('td', {'class': 'td-long'})
    pravni_veta = pravni_veta_cell.get_text(strip=True) if pravni_veta_cell else ''

    # Find the link to the RTF file in the first cell
    rtf_link = None
    link_tags = cells[0].find_all('a')
    for link_tag in link_tags:
        href = link_tag.get('href')
        if href and href.lower().endswith('.rtf?openelement'):
            rtf_link = 'https://rozhodnuti.nsoud.cz' + href
            break

    if not rtf_link:
        return "Link for decision not found."

    # Download the RTF file
    rtf_response = requests.get(rtf_link)
    if rtf_response.status_code != 200:
        return "Failed to download the text of the decision."

    # Extract text from the RTF content
    try:
        rtf_text = rtf_to_text(rtf_response.content.decode('latin-1'))
    except Exception as e:
        rtf_text = f"Failed to extract text from RTF: {e}"

    # Assemble the result text
    result = f"File No. {file_no},\nKategorie: {kategorie},\nPrávní věta': {pravni_veta},\nText: {rtf_text}"

    return result
