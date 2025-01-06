import requests
import bs4

import pics2vid
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

url = "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/CONUS/14/"
size = (1250, 750)

response = requests.get(url)
soup = bs4.BeautifulSoup(response.text, "html.parser")

links = soup.find_all("a")
filtered_links = [
    url + link.get("href")
    for link in links
    if link.get("href").endswith(f"{size[0]}x{size[1]}.jpg")
]

filtered_links = filtered_links[:20]

# print(filtered_links)

asyncio.run(pics2vid.encode_images_to_gif(filtered_links, output_file="output.gif", max_concurrency=5))