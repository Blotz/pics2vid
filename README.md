# pics2vid

Simple library which converts a list of image urls to video.
![example output](https://raw.githubusercontent.com/Blotz/pics2vid/refs/heads/main/data/output.gif)

Provides a simple interface for downloading images asynchronously & in order.

Images are stored in a buffer until all previous images have been downloaded.

```python
import asyncio
from pics2vid import encode_images_to_video

async def main():
    await encode_images_to_video(links, output_file="output.mp4", max_concurrency=5)
```

```python
import asyncio
from pics2vid import encode_images_to_gif

async def main():
    await encode_images_to_gif(links, output_file="output.gif", max_concurrency=5)
```

Write your own!
```python
import asyncio
from pics2vid import download_images_concurrently

async def main():
    async for image_buffer in download_images_concurrently(links, max_concurrency):
        image_buffer.read()
```
