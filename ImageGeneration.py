import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import get_key
import os
from time import sleep

def open_images(prompt):
    folder_path = r"Data"
    prompt = prompt.replace(" ", "_")

    Files = [f"{prompt}{i}.jpg" for i in range(1, 5)]

    for jpg_file in Files:
        image_path = os.path.join(folder_path, jpg_file)

        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                print(f"Opening image: {image_path}")
                img.show()
                sleep(1)
            except IOError:
                print(f"Unable to open {image_path}")
        else:
            print(f"Image file {image_path} does not exist.")


API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
headers = {"Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}"}


async def query(payload):
    retries = 5  # Number of retries for model loading
    while retries > 0:
        response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return response.content
        elif response.status_code == 503:  # Model loading error
            print(f"Model is loading. Retrying in 10 seconds...")
            await asyncio.sleep(10)  # Wait before retrying
            retries -= 1
        elif response.status_code == 429:  # Rate limit
            print(f"Rate limit exceeded. Retrying in 30 seconds...")
            await asyncio.sleep(30)
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    print("Model failed to load after multiple retries.")
    return None


async def generate_images(prompt: str):
    tasks = []

    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, seed={randint(0, 1000000)}",
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)
        await asyncio.sleep(15)  # Add delay between requests to avoid rate limit

    image_bytes_list = await asyncio.gather(*tasks)

    folder_path = r"Data"
    os.makedirs(folder_path, exist_ok=True)  # Ensure the Data folder exists

    for i, image_bytes in enumerate(image_bytes_list):
        if image_bytes:
            file_path = os.path.join(folder_path, f"{prompt.replace(' ','_')}{i + 1}.jpg")
            with open(file_path, "wb") as f:
                f.write(image_bytes)


def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_images(prompt)


while True:
    try:
        with open(r"Frontend\Files\ImageGeneration.data", "r") as f:
            Data: str = f.read()

        Prompt, Status = Data.split(",")

        if Status.strip() == "True":
            print("Generating Image...")
            GenerateImages(prompt=Prompt.strip())

            with open(r"Frontend\Files\ImageGeneration.data", "w") as f:
                f.write("False,False")
            break

        else:
            sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        sleep(1)
