import aiohttp
import asyncio
import urllib.parse
from urllib.parse import urlparse, parse_qs
import json
import re
import os
import requests
from bs4 import BeautifulSoup


class Session:
    def __init__(self, token):
        self.token = token


async def login(url, token):
    # Send authentication request
    async with aiohttp.ClientSession() as session:
        url = f"{url}api/v1/auth/login"
        headers = {"User-Agent": "CTFer"}
        data = {
            "teamToken": token,
        }

        async with session.post(url, json=data, headers=headers, allow_redirects=False) as response:
            response_data = await response.json()
            token = response_data['data']['authToken']
            # print(response_data)
            # print(token)
            return Session(token=token)


async def down(session, json_data):
    cleaned_json_data = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', json_data)

    data = json.loads(cleaned_json_data)
    async with aiohttp.ClientSession() as session:
        for challenge in data['data']:
            files = challenge['files']
            directory = f"{challenge['category']}/{challenge['name']}"
            os.makedirs(directory, exist_ok=True)
            # url = file['url']
            for file_obj in files:
                url = file_obj['url']
                name_of_file = file_obj['name']
                async with session.get(url) as response:
                    file_data = await response.read()
                file_path = os.path.join(directory, name_of_file)
                with open(file_path, 'wb') as f:
                    f.write(file_data)
            print(f"Downloaded {challenge['name']} to {directory}")


def create_CTF_folder(url):
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.head.title.string
    # Replace special characters with underscores (_)
    folder_name = re.sub(r'\W+', '_', title)
    if os.path.exists(folder_name) == False:
        os.mkdir(folder_name)
    os.chdir(folder_name)
    print(f'[*] Create {folder_name} folder done')


async def main(url, token):
    # Authorize if needed
    session = await login(url, token)
    headers = {"User-Agent": "Eruditus",
               "Authorization": "Bearer " + session.token}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{url}api/v1/challs") as response:
            response_data = await response.json()
            json_str = json.dumps(response_data, indent=4)
            await down(session, json.dumps(response_data))


def token_handling(token):
    parsed_token = urlparse(token)
    token = parse_qs(parsed_token.query)["token"][0]
    return urllib.parse.unquote(token)


if __name__ == "__main__":
    url = input('URL: ')
    token = input('token: ')
    create_CTF_folder(url)
    token = token_handling(token)
    asyncio.run(main(url, token))


