from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
from urllib.parse import urljoin


def get_page(url):
    '''
    Function wich make get request on given url and returns response text
    :param url:
    :return:
    '''
    headers = {
        'authority': url,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru-UA,ru;q=0.9,uk-UA;q=0.8,uk;q=0.7,ru-RU;q=0.6,en-US;q=0.5,en;q=0.4',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    try:
        print(f"Making request to {url}")
        response = requests.get(f"https://{url}", headers=headers, verify=False)
        if not response.status_code == 200:
            return None
        return response.text
    except Exception as e:
        print(f"Exception occured in (get_page): {e}")


def find_contact_link(soup, base_url):
    links = soup.find_all('a')

    for link in links:
        link_text = link.get_text()
        link_href = link.get('href')
        try:
            if link_text and 'contact' in link_text.lower():
                contact_link = link_href
            elif link_href and 'contact' in link_href.lower():
                contact_link = link_href
            else:
                continue

            if not contact_link.startswith(('http://', 'https://')):
                contact_link = urljoin(base_url, contact_link)
            else:
                contact_link = contact_link.split('://', 1)[-1]
                return contact_link
        except Exception as e:
            print("Something went wrong: ", e)
    return None


def email_getter(soup: BeautifulSoup, raw_data: str):
    def get_emails_soup():
        all_tags = soup.find_all(True)
        email_list = set()
        pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        for t in all_tags:
            res = re.findall(pattern, t.text)
            for n in res:
                email_list.add(n)
        print(f"Emails from soup: {email_list}")
        return email_list

    def get_emails_raw():
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        email_matches = email_pattern.findall(raw_data)
        print(f"Emails from data: {email_matches}")
        return email_matches

    result = list(set([*get_emails_raw(), *get_emails_soup()]))
    print(f"Emails result search: {result}")
    return result


def get_numbers(soup: BeautifulSoup, raw_data: str):
    def get_numbers_soup():
        numbers = set()
        all_tags = soup.find_all(True)
        phone_pattern = re.compile(r'(\+?\d{1,3}\s?-?\(?\d{2,3}\)?\s?-?\d{2,3}\s?-?\d{2,3}\s?-?\d{2,3})')
        for t in all_tags:
            phone_matches = re.findall(phone_pattern, t.text)
            for p_m in phone_matches:
                numbers.add(p_m)
        print(f"Phone numbers from soup: {numbers}")
        return numbers

    def get_numbers_row():
        phone_pattern = re.compile(r'(\+?\d{1,3}\s?-?\(?\d{2,3}\)?\s?-?\d{2,3}\s?-?\d{2,3}\s?-?\d{2,3})')
        phone_matches = phone_pattern.findall(raw_data)
        print(f"Phone numbers from data: {phone_matches}")
        return phone_matches

    result = list(set([*get_numbers_row(), *get_numbers_soup()]))
    print(f"Result phone numbers: {result}")
    return result


def get_social_networks(soup: BeautifulSoup):
    social_networks = {}
    social_links = soup.find_all('a', href=True)  # find all 'a' tags with href
    for link in social_links:
        href = link['href']
        if 'facebook.com' in href:
            social_networks['facebook'] = href
        elif 'twitter.com' in href:
            social_networks['twitter'] = href
        elif 'instagram.com' in href:
            social_networks['instagram'] = href
        elif 'linkedin.com' in href:
            social_networks['linkedin'] = href
        elif 'skype:' in href:
            social_networks['skype'] = href.split(':')[-1]
    return social_networks


def parse_page(data, url):
    '''
    Because of uniqueness of every page parse page using regular expressions then return dictionary with results
    :param data:
    :param url:
    :return:
    '''
    soup = BeautifulSoup(data, 'lxml')
    contacts = {}

    contact_us_page = find_contact_link(soup, url)
    if contact_us_page:
        new_data = get_page(contact_us_page)
        if new_data:
            soup = BeautifulSoup(new_data, "lxml")

    phone_matches = get_numbers(soup, data)
    if phone_matches:
        contacts['phone'] = ", ".join(phone_matches[:3])

    # email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    email_matches = email_getter(soup, data)
    if email_matches:
        contacts['email'] = ", ".join(email_matches)

    address_tag = soup.find('address')
    if address_tag:
        contacts['address'] = address_tag.get_text()

    # skype_pattern = re.compile(r'skype:[\w\.-]+')
    # skype_matches = skype_pattern.findall(data)
    # if skype_matches:
    #     contacts['skype'] = skype_matches[0].split(':')[-1]

    social_networks = get_social_networks(soup)
    contacts.update(social_networks)
    return contacts


def get_urls(table_name):
    '''
    Parse all urls without duplicates from excel file
    :return:
    '''
    urls_result = set()
    df = pd.read_excel("USA Services.xlsx")
    urls_col = df["website"]
    for row in urls_col:
        if pd.isna(row):
            continue
        urls = row.split(", ")
        for url in urls:
            urls_result.add(url)
    return urls_result


def process_page(url, df: pd.DataFrame, location, keyword):
    '''
    Receive page text then parsing it and append into result file
    :param url:
    :param df:
    :param location:
    :param keyword:
    :return:
    '''
    data = get_page(url)
    # new_row = pd.DataFrame(index=[0])
    if not data:
        return df
    else:
        data = parse_page(data, url)
    #     for key, value in data.items():
    #         new_row.loc[0, key] = value
    # new_row.loc[0, 'website'] = url
    # print(new_row)
    data["website"] = url
    data["location"] = location
    data["keyword"] = keyword
    df.loc[len(df.index)] = data
    print(data)
    return df


def main():
    '''
    Entry point of program
    Receive all urls from the excel file and start process each url using threads for time saving
    :return:
    '''
    urls = list(get_urls(""))
    # process_per_iter = 10
    sites_range = len(urls)
    existing_table = pd.read_excel("USA Services.xlsx")
    try:
        for i in range(sites_range):
            existing_table = process_page(urls[i], existing_table, "Florida", "Chiropractor")
    except Exception as e:
        print(f"Something went wrong in (main): {e}")
    finally:
        existing_table.to_excel("USA Services.xlsx", index=False)
        print(existing_table)


if __name__ == "__main__":
    main()


