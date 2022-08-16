import json
import os.path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag


# function to get URLs from page
def get_api_page_urls(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    # finds all links to API/API Standards as listed on the page
    links = [a['href'] for a in soup.find_all('a', href=True)]
    filtered_divs = list(filter(lambda x: '/developer/api-catalogue/' in x, links))
    beg = 'https://digital.nhs.uk'
    api_page_urls = []
    for link in filtered_divs:
        url_combined = beg + link
        api_page_urls.append(url_combined)
    return api_page_urls


# function to pull out the title of the API
def get_api_title(api_url):
    page = requests.get(api_url)
    soup = BeautifulSoup(page.text, 'html.parser')
    return soup.find(class_='nhsd-t-heading-xxl nhsd-!t-margin-bottom-0').text


# function to pull out all information between h2 headers
def get_api_info(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    headers_text_dict = {}
    for header in soup.find_all('h2'):
        contain = ''
        nextNode = header
        while True:
            nextNode = nextNode.nextSibling
            if nextNode is None:
                if 'overview' in header.text.lower():
                    svgs = soup.find_all('svg')
                    for svg in svgs:
                        if svg.find_next_sibling('div', 'nhsd-!t-margin-bottom-6') is not None:
                            contain = contain + ' ' + svg.find_next_sibling('div', 'nhsd-!t-margin-bottom-6').get_text(
                                strip=True).strip()
                break
            if isinstance(nextNode, NavigableString):
                pass
            if isinstance(nextNode, Tag):
                if nextNode.name == "h2":
                    break
                contain = contain + ' ' + nextNode.get_text(strip=True).strip()
        headers_text_dict[header.text.strip().lower()] = contain

    return headers_text_dict


# pulls out the data we need to fit our metadata model
def create_filtered_dict(apis, unfiltered_dict, title):
    new_dict = {}
    description = unfiltered_dict['overview']
    new_dict['name'] = title
    new_dict['description'] = description
    new_dict['url'] = apis
    new_dict['contact'] = 'https://digital.nhs.uk/developer/help-and-support'
    new_dict['organisation'] = 'NHS Digital'
    new_dict['documentation-url'] = apis
    return new_dict


def get_list_of_api_details():
    filtered_list = []
    url = 'https://digital.nhs.uk/developer/api-catalogue'
    api_urls = get_api_page_urls(url)
    for apis in api_urls:
        title = get_api_title(apis)
        if 'standard' not in title:
            unfiltered_dict = get_api_info(apis)
            filtered_dict = create_filtered_dict(apis, unfiltered_dict, title)
            filtered_list.append(filtered_dict)
    return filtered_list


def create_v1alpha_json_object(filtered_list):
    json_data = {'api-version': "api.gov.uk/v1alpha"}
    apis = []
    for data in filtered_list:
        api = {'api-version': "api.gov.uk/v1alpha", 'data': data}
        apis.append(api)
    json_data['apis'] = apis
    return json.dumps(json_data, indent=4)


def write_json_to_file(v1alpha_json_object):
    with open(os.path.join('nhs-digital', 'apis'), 'w') as file:
        file.write(v1alpha_json_object)


if __name__ == '__main__':
    v1alpha_json_object = create_v1alpha_json_object(get_list_of_api_details())
    write_json_to_file(v1alpha_json_object)
