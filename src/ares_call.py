from typing import Any
import httpx

BASE_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/"
HEADERS = {"Content-Type": "application/json","accept": "application/json"}

def get_current(entries):
    for entry in entries:
        if 'datumVymazu' not in entry:
            return entry
    return None

class ARES:

    @staticmethod
    async def get_base_data(company_name: str) -> str | None:
        """Make a request to the ARES API the search for the given company."""
        url = "/ekonomicke-subjekty/vyhledat"
        data = {"start": 0,"pocet": 10,"razeni": ["obchodniJmeno"],"obchodniJmeno": company_name}
        response = await ARES.make_request("POST", data, url)

        """ Checks if there is any company returned. """
        if response["pocetCelkem"] == 0:
            response_text = f"No entries found for {company_name}"
            return response_text

        """ Checks if there are more that one company """
        if response["pocetCelkem"] > 1:
            response_text = f"For {company_name} there are multiple entries:"
            for i in range(len(response["ekonomickeSubjekty"])):
                company_info = f" company {response['ekonomickeSubjekty'][i]['obchodniJmeno']}, Id. No. {response['ekonomickeSubjekty'][i]['ico']},"
                response_text += company_info
            response_text += ". Ask which do they want."
            return response_text

        """ Checks if the company has entry in Commercial Register, if yes, fetches the data. """
        if response["ekonomickeSubjekty"][0]["seznamRegistraci"]["stavZdrojeVr"] == "AKTIVNI":
            additional_data = await ARES.make_request("GET", endpoint_url=f"/ekonomicke-subjekty-vr/{response['ekonomickeSubjekty'][0]['ico']}")
            formatted_data = ARES.extract_vr_info(additional_data)
            response_text = ARES.format_vr_data(formatted_data)
            return response_text

        """ If there is no entry in Commercial Register, return basic data from ARES only. """
        response_text = ARES.format_base_info(response, company_name)
        return response_text

    @staticmethod
    async def make_request(method: str, data: dict | None = None, endpoint_url: str = ""):

        url = BASE_URL + endpoint_url

        async with httpx.AsyncClient() as client:
            response = await client.request(url=url, method=method, headers=HEADERS, json=data, timeout=30.0)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def format_base_info(data: dict, company_name: str) -> str:
        """Format an alert feature into a concise string."""
        data: list = data["ekonomickeSubjekty"]
        results: list = []
        for i in range(len(data)):
            results.append(
                f"Company name: {data[i].get('obchodniJmeno', 'Unknown')}\n"
                f"Company address: {data[i]['sidlo'].get('textovaAdresa', 'Unknown')}\n"
                f"Company identification number (in Czech IČO): {data[i].get('ico', 'Unknown')}\n"
                "---\n"
            )
        return f"Information from public register for {company_name}:\n" + "".join(results)

    @staticmethod
    def extract_vr_info(data: dict) -> dict:

        company_info = {}

        """ Gets current name """
        obchodni_jmeno = get_current(data['zaznamy'][0]['obchodniJmeno'])
        if obchodni_jmeno:
            company_info['company_name'] = obchodni_jmeno['hodnota']
        else:
            company_info['company_name'] = "Unknown"

        """ Extracts ICO """
        current_ico = get_current(data['zaznamy'][0]['ico'])
        if current_ico:
            company_info['ico'] = data['icoId']

        """ Gets current address """
        adresy = data['zaznamy'][0].get('adresy', [])
        for address_entry in adresy:
            if address_entry['typAdresy'] == 'SIDLO' and 'datumVymazu' not in address_entry:
                company_info['address'] = address_entry['adresa']['textovaAdresa']
                break

        """ Gets current members of statutory bodies """
        statutory_bodies = get_current(data['zaznamy'][0].get('statutarniOrgany', []))
        current_statutory_bodies = []
        body_members = statutory_bodies.get('clenoveOrganu', [])
        for member in body_members:
            if 'datumVymazu' not in member:
                person = member.get('fyzickaOsoba', member.get('pravnickaOsoba', {}))
                function = member['clenstvi']['funkce'].get('nazev', '')
                if person:
                    jmeno = person.get('jmeno', '')
                    prijmeni = person.get('prijmeni', '')
                    obchodni_jmeno = person.get('obchodniJmeno', '')
                    if jmeno or prijmeni:
                        name = f"{jmeno} {prijmeni}, funkce: {function}".strip()
                    else:
                        name = f"{obchodni_jmeno}, funkce: {function}".strip()
                    current_statutory_bodies.append(name)
        company_info['statutory_bodies'] = current_statutory_bodies

        """ Gets current ways of acting """
        company_info['ways_of_acting'] = ''
        way_of_acting = statutory_bodies.get('zpusobJednani', [])
        for entry in way_of_acting:
            if 'datumVymazu' not in entry:
                company_info['ways_of_acting'] = entry['hodnota']
                break

        return company_info

    @staticmethod
    def format_vr_data(data: dict) -> str:
        """Format data from dictionary to string"""
        response_text = f"Information from Czech Commercial register for {data['company_name']}:\n---\nCompany name: {data['company_name']}\nCompany seat address: {data['address']}\nCompany identification number (in Czech IČO): {data['ico']}\nCurrent members of the statutory body: {', '.join(member for member in data['statutory_bodies'])}\nCurrent way of acting on behalf of the company: {data['ways_of_acting']}\n---\n"

        return response_text