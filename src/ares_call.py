from typing import Any
import httpx
from Scripts.bottle import response

BASE_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/"
HEADERS = {"Content-Type": "application/json","accept": "application/json"}

def get_current(entries: list) -> Any:
    """ Returns current entries. """
    for entry in entries:
        if 'datumVymazu' not in entry:
            return entry
    return None

class ARES:

    @staticmethod
    async def get_base_data(company_name: str) -> str | None:
        """Make a request to the ARES API the search for the given company."""

        url: str = "/ekonomicke-subjekty/vyhledat"
        data: dict = {"start": 0,"pocet": 10,"razeni": ["obchodniJmeno"],"obchodniJmeno": company_name}
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
        """ Makes API request to ARES."""
        url: str = BASE_URL + endpoint_url

        async with httpx.AsyncClient() as client:
            response = await client.request(url=url, method=method, headers=HEADERS, json=data, timeout=30.0)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def format_base_info(data: dict, company_name: str) -> str:
        """Format base information into a concise string."""
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
        """ Extracts needed data from API response to dictionary. """

        company_info: dict = {}

        """ Gets current name """
        company_name = get_current(data['zaznamy'][0]['obchodniJmeno'])
        if company_name:
            company_info['company_name'] = company_name['hodnota']
        else:
            company_info['company_name'] = "Unknown"

        """ Extracts ICO """
        current_ico = get_current(data['zaznamy'][0]['ico'])
        if current_ico:
            company_info['ico'] = data['icoId']

        """ Gets current address """
        adresy: list = data['zaznamy'][0].get('adresy', [])
        for address_entry in adresy:
            if address_entry['typAdresy'] == 'SIDLO' and 'datumVymazu' not in address_entry:
                company_info['address'] = address_entry['adresa']['textovaAdresa']
                break

        """ Gets current members of statutory bodies """
        statutory_bodies_list: list = data['zaznamy'][0].get('statutarniOrgany', [])
        result_list: list = []

        for organ in statutory_bodies_list:
            name_of_body = organ.get('nazevOrganu', '')
            body_members = organ.get('clenoveOrganu', [])
            members_list = []

            for member in body_members:
                if 'datumVymazu' not in member:
                    # Get person details
                    person = member.get('fyzickaOsoba', member.get('pravnickaOsoba', {}))
                    if person:
                        name = person.get('jmeno', '')
                        surname = person.get('prijmeni', '')
                        company_name = person.get('obchodniJmeno', '')
                        if name or surname:
                            name = f"{name} {surname}".strip()
                        else:
                            name = company_name.strip()
                    else:
                        name = ''

                    """ Get function name if included. """
                    function = member.get('clenstvi', {}).get('funkce', {}).get('nazev', '')
                    if function:
                        name_with_function = f"{name}, {function}"
                    else:
                        name_with_function = name

                    members_list.append(name_with_function)

            statutory_bodies = {
                'name_of_body': name_of_body,
                'members': members_list
            }

            """ Include 'ways_of_acting' if 'zpusobJednani' is present"""
            ways_of_acting = organ.get('zpusobJednani', [])
            for entry in ways_of_acting:
                if 'datumVymazu' not in entry:
                    statutory_bodies['ways_of_acting'] = entry.get('hodnota', '')
                    break  # Use the first current 'zpusobJednani'

            result_list.append(statutory_bodies)

        company_info["statutory_bodies"] = result_list

        return company_info

    @staticmethod
    def format_vr_data(data: dict) -> str:
        """Format data from dictionary to string"""

        response_text: str = f"Information from Czech Commercial register for {data['company_name']}:\n---\nCompany name: {data['company_name']}\nCompany seat address: {data['address']}\nCompany identification number (in Czech IČO): {data['ico']}\n"
        for body in data['statutory_bodies']:
            response_text += f"{body['name_of_body']} - {', '.join(member for member in body['members'])}"
            if "ways_of_acting" in body:
                response_text += f" - Way of acting: {body['ways_of_acting']}\n"
            else:
                response_text += "\n"
        response_text += "---\n"
        return response_text