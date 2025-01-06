import asyncio
import aiohttp
import ffmpeg
import heapq
import io
import logging

from pics2vid import __name__ as name

OUTPUT_FILE = "output.mp4"
MAX_CONCURRENCY = 50

logger = logging.getLogger(name)


async def get_image(url: str, session: aiohttp.ClientSession, idx: int):
    try:
        async with session.get(url=url) as response:
            buffer = io.BytesIO(await response.read())
            return (idx, buffer)
    except Exception as e:
        logger.error(f"Unable to get url {idx} {url} due to {e.__class__}.")
        return idx, None


async def in_order_as_completed(n: int, coros: list[asyncio.Task]):
    # limit the number of requests to n using a semaphore
    semaphore = asyncio.Semaphore(n)

    async def process_concurrent_task(coro):
        async with semaphore:
            result = await coro
            return result

    # call the tasks in order so the semaphore locks the tasks in order.        
    tasks = (asyncio.create_task(process_concurrent_task(coro)) for coro in coros)
    # as_completed runs all the tasks concurrently, but the semaphore
    # will limit the number of tasks running at once.
    for task in asyncio.as_completed(tasks):
        yield task


def process_buffer(links: list[str], frame_count: int, index: int, frame_buffer: heapq):
    # if the newest frame is the correct frame, write it to the ffmpeg writer
    while len(frame_buffer) > 0 and frame_buffer[0][0] == frame_count:
        request_data = heapq.heappop(frame_buffer)
        frame_count += 1
        logger.debug(f"Downloading image {index}/{len(links)} Frame buffer {frame_count}/{len(frame_buffer)}")
        # if the request failed, skip it
        if request_data[1] is None:
            continue

        # This could be overwritten
        # writer.stdin.write(request_data[1].read())
        yield request_data[1]
        request_data[1].close()


async def download_images_concurrently(links: str, max_concurrency: int):
    async with aiohttp.ClientSession() as session:
        # Create list of coroutines to download images
        tasks = (*(get_image(url, session, idx) for idx, url in enumerate(links)),)

        # Create a frame buffer to store the images
        frame_count = 0
        index = 0
        frame_buffer = heapq.nsmallest(max_concurrency, [], key=lambda x: x[0])

        # Download images and write to ffmpeg writer
        async for r in in_order_as_completed(max_concurrency, tasks):
            index += 1
            logger.debug(f"Downloading image {index}/{len(links)} Frame buffer {frame_count}/{len(frame_buffer)}")
            result = await r

            # Push the result into the frame buffer
            heapq.heappush(frame_buffer, result)
            # Process the frame buffer
            for frame in process_buffer(links, frame_count, index, frame_buffer):
                yield frame
                frame_count += 1


async def encode_images_to_video(links: list[str], output_file=OUTPUT_FILE, max_concurrency=MAX_CONCURRENCY):
    # Create ffmpeg writer
    writer = (
        ffmpeg.input("pipe:", format="image2pipe", framerate=24)
        .output(output_file, vcodec="libx264", pix_fmt="yuv420p", preset="fast")
        .run_async(pipe_stdin=True, overwrite_output=True, quiet=True)
    )
    async for frame in download_images_concurrently(links, max_concurrency):
        writer.stdin.write(frame.read())
    
    # Wait for the encoding to finish
    writer.stdin.close()
    writer.wait()


async def encode_images_to_gif(links: list[str], output_file=OUTPUT_FILE, max_concurrency=MAX_CONCURRENCY):
    # Create ffmpeg writer
    writer = (
        ffmpeg.input("pipe:", format="image2pipe", framerate=24)
        .output(output_file, vcodec="gif", pix_fmt="yuv420p", preset="fast")
        .run_async(pipe_stdin=True, overwrite_output=True, quiet=True)
    )
    async for frame in download_images_concurrently(links, max_concurrency):
        writer.stdin.write(frame.read())
    
    # Wait for the encoding to finish
    writer.stdin.close()
    writer.wait()
