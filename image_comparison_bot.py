import os
import cv2
import requests
import numpy as np
import pandas as pd
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from minio import Minio, S3Error
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
import json
import io
import asyncio
import aiohttp
from dotenv import load_dotenv
import logging
import imagehash
import discord
from discord import app_commands
from discord.ext import commands

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    filename='image_comparison_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ImageComparison:
    
    def __init__(self):
        """ Initializes the ImageComparison class and automatically generates folder based on date-time. """
        
        self.bucket_name = 'test'   #---> Replace with your bucket name
       
        self.minio_client = Minio(
            endpoint=os.getenv("minio_endpoint"),
            access_key=os.getenv("accesskey"),
            secret_key=os.getenv("secretkey"),
            secure=True
        )
        
        current_time = datetime.now().strftime('%Y-%m-%d(%H-%M-%S)') # Creating folder name with current datetime
        
        self.dataset_name = f"Dataset_{current_time}"
        
        self.dataset_folder = os.path.join(os.getcwd(), self.dataset_name)
        os.makedirs(self.dataset_folder, exist_ok=True)
        
        print(f"Dataset folder created: {self.dataset_name}")

    
    
    async def fetch_images_from_discord(self, channel_id):
        """_summary_

        Args:
            channel_id (int): channel_id
        """       


        """ Fetches images from Discord channel and uploads them directly to MinIO. """
        
        self.channel_id = channel_id
        
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
        
        headers = {"Authorization": os.getenv("DISCORD_TOKEN")}  # ----> Replace with your Authorization Token

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    
                    if response.status == 200:
                        
                        latest_message = await response.json()
                        
                        image_urls = []
                        
                        attachments = latest_message[0].get('attachments')
                        
                        if attachments:
                            
                            for attachment in attachments:
                                img_url = attachment.get('url')
                                image_urls.append(img_url)
                        
                        tasks = [self.upload_image_to_minio(session, img_url) for img_url in image_urls]
                        await asyncio.gather(*tasks)
                        
                    else:
                        await self.send_discord_message(f"Failed to fetch messages from Discord: Status {response.status}")
            
            except Exception as e:
                
                await self.send_discord_message(f"An error occurred while fetching images from Discord: {e}")

        await self.download_images_from_minio()

    
    
    async def upload_image_to_minio(self, session, image_url):
        """_summary_

        Args:
            session (_type_): _description_
            image_url (url): Image url
        """       
        
        
        """ Downloads an image from a URL and uploads it directly to MinIO without saving locally """
        
        image_name = os.path.basename(image_url)
        try:
            
            async with session.get(image_url) as response:
                
                if response.status == 200:
                    image_data = io.BytesIO(await response.read())  #Store the image temporarily in the RAM
                    minio_object_name = f'image dataset/Image-compare-dataset/{self.dataset_name}/{image_name}'  # ----> Replace with your file path
                    self.minio_client.put_object(
                        self.bucket_name,
                        minio_object_name,
                        data=image_data,
                        length=image_data.getbuffer().nbytes,
                        content_type='image/jpeg'
                    )
                    
                    print(f"Uploaded {image_name} to MinIO folder {self.dataset_name}")
        
        except Exception as e:
            print(f"Failed to upload {image_name} to MinIO: {e}")

    
    
    async def download_images_from_minio(self):
        """ Downloads images from the automatically created MinIO folder """
        
        objects = self.minio_client.list_objects(self.bucket_name, 
                                                 prefix=f'image dataset/Image-compare-dataset/{self.dataset_name}', # ----> Replace with your file path
                                                 recursive=True) 
        
        async with aiohttp.ClientSession() as session:
            
            tasks = [self.download_and_save_image(session, obj.object_name) for obj in objects]
            
            await asyncio.gather(*tasks)

        
        await self.send_discord_message("Images Started Processing...")
        
        await self.compare_images_and_save_results()


    async def download_and_save_image(self, session, object_name):
        """_summary_

        Args:
            session (_type_): _description_
            object_name (_type_): Images name
        """        


        """ Downloads an image from MinIO and saves it locally """
        try:
            presigned_url = self.minio_client.get_presigned_url(bucket_name=self.bucket_name, object_name=object_name, expires=timedelta(days=7), method='GET')
            
            async with session.get(presigned_url) as response:
                
                if response.status == 200:
                    file_path = os.path.join(self.dataset_folder, os.path.basename(object_name.split('?')[0]))
                    
                    with open(file_path, 'wb') as file:
                        file.write(await response.read())
                    print(f"Downloaded {object_name} to {file_path}")
        
        except Exception as e:
            print(f"Failed to download {object_name}: {e}")

    
    
    def detect_and_correct_rotation(self, image):
        """Rotates the image to portrait orientation if it is in landscape orientation and corrects for upside-down rotation."""

        # Convert the image to OpenCV format (for edge detection)
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Convert to grayscale for edge detection
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Use Canny edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Use Hough Transform to detect lines
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        # If no lines detected, return original
        if lines is None:
            print("No lines detected, returning original orientation.")
            return image

        # Find predominant angle from detected lines
        angles = []
        for line in lines:
            for rho, theta in line:
                angle = np.rad2deg(theta) - 90
                if -180 < angle < 180:
                    angles.append(angle)

        # Calculate the median angle
        median_angle = np.median(angles) if angles else 0

        # Determine rotation correction needed to achieve portrait orientation
        width, height = image.size
        
        if width > height:  # Image is in landscape mode
            
            if median_angle < 0:  # Right-facing landscape
                rotated_image = image.rotate(-90, expand=True)
                print("Rotated -90° to make portrait from right-facing landscape.")
            
            else:  # Left-facing landscape
                rotated_image = image.rotate(90, expand=True)
                print("Rotated 90° to make portrait from left-facing landscape.")
        
        elif median_angle > 85 or median_angle < -85:
            # If portrait but upside down, rotate 180° to correct
            rotated_image = image.rotate(180, expand=True)
            print("Image rotated 180° to correct upside-down portrait orientation.")
        
        else:
            rotated_image = image
            print("Image is already correctly oriented in portrait mode.")
        
        #rotated_image.show()
        return rotated_image


    def compare_rotated_images(self, image_path1, image_path2):
        """Compare two images using block-wise perceptual hashing (pHash).
        
        Args:
            image_path1 (str): Path to the first image.
            image_path2 (str): Path to the second image.
            block_size (int): Number of blocks to divide the image into (block_size x block_size).
            hash_size (int): Size of the Wavelet Hash for each block.
        
        Returns:
            float: Overall similarity percentage between the two images.
        """
        block_size=50
        
        # Small Hash Sizes (4x4, 8x8): Good for broad similarity detection (e.g: duplicate detection or large-scale comparison).
        # Larger Hash Sizes (16x16, 32x32): Ideal for detecting subtle differences or comparing images with finer detail.
        hash_size=16  #8

        # haar: Default and often effective for general use, as it captures broad patterns and details.
        # db4: Slightly more complex and can capture finer structural details, useful if images contain rich textures or are highly detailed.
        mode = 'haar' #db4

        # Load images
        img1 = Image.open(image_path1)
        img2 = Image.open(image_path2)

        img1 = self.detect_and_correct_rotation(img1)
        img2 = self.detect_and_correct_rotation(img2)

        # Ensure both images are of the same size for block-wise comparison
        if img1.size != img2.size:
            img2 = img2.resize(img1.size)

        # Get block dimensions
        width, height = img1.size

        block_width, block_height = width // block_size, height // block_size
        
        # Initialize variables for similarity calculation
        total_blocks = block_size ** 2

        matching_blocks = 0

        # Loop through each block
        for i in range(block_size):
            for j in range(block_size):
               
                # Define the area for each block
                left = i * block_width  
                upper = j * block_height
                right = left + block_width
                lower = upper + block_height
                
                # Crop each block from both images
                block_img1 = img1.crop((left, upper, right, lower))
                block_img2 = img2.crop((left, upper, right, lower))

                # Compute wHash for each block
                hash1 = imagehash.whash(block_img1, hash_size=hash_size, mode=mode)
                hash2 = imagehash.whash(block_img2, hash_size=hash_size, mode=mode)

                # Calculate Hamming distance and define similarity threshold
                hamming_distance = hash1 - hash2

                max_distance = hash_size ** 2  # Maximum possible Hamming distance
                
                similarity_percentage = (1 - hamming_distance / max_distance) * 100
                
                # Define a similarity threshold (e.g: >85% means the blocks are similar)
                if similarity_percentage > 85:
                    matching_blocks += 1

        # Calculate overall similarity as the percentage of matching blocks
        overall_similarity = (matching_blocks / total_blocks) * 100
        
        print(f"Overall similarity (block-wise): {overall_similarity:.2f}%")
        return overall_similarity

    async def compare_images_and_save_results(self):
        """ Compares all images in the folder and saves results """
        
        images = [os.path.join(self.dataset_folder, f) for f in os.listdir(self.dataset_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        df = pd.DataFrame(columns=['Image 1', 'Image 2', 'Similarity (%)'])

        for i in range(len(images)):
            for j in range(i + 1, len(images)):
                image_path1 = images[i]
                image_path2 = images[j]
                
                similarity = self.compare_rotated_images(image_path1, image_path2)
                
                df = df._append({'Image 1': os.path.basename(image_path1), 'Image 2': os.path.basename(image_path2), 'Similarity (%)': f"{similarity:.2f}"}, ignore_index=True)

        output_dir = os.path.join(os.getcwd(), 'Comparison_Results')
        os.makedirs(output_dir, exist_ok=True)
        
        csv_filename = os.path.join(output_dir, f"{self.dataset_name}_comparison_results.csv")
        
        df.to_csv(csv_filename, index=False)

        print(f"Comparison results saved to {csv_filename}")

        await self.send_csv_to_discord(csv_filename)

    
    
    async def send_csv_to_discord(self, csv_file_path):
        """ Sends the generated CSV file to the specified Discord channel """
        
        url = f"https://discord.com/api/v9/channels/{self.channel_id}/messages"
        
        headers = {"Authorization": os.getenv("DISCORD_TOKEN")}

        async with aiohttp.ClientSession() as session:
            try:
                with open(csv_file_path, 'rb') as f:
                    
                    form = aiohttp.FormData()
                    
                    form.add_field('file', f, filename=os.path.basename(csv_file_path))
                    
                    async with session.post(url, headers=headers, data=form) as response:
                        
                        if response.status == 200:
                            print(f"Successfully sent {os.path.basename(csv_file_path)} to Discord channel {self.channel_id}.")
                        else:
                            print(f"Failed to send CSV to Discord: {response.status} {await response.text()}")
            
            except Exception as e:
                print(f"Error sending CSV to Discord: {e}")

    
    
    async def send_discord_message(self, content):
        """_summary_

        Args:
            content (str): message
        """       

        """ Sends a text message to the specified Discord channel """
        
        url = f"https://discord.com/api/v9/channels/{self.channel_id}/messages"
        
        headers = {"Authorization": os.getenv("DISCORD_TOKEN")}
        
        data = {"content": content}

        async with aiohttp.ClientSession() as session:
            
            async with session.post(url, headers=headers, json=data) as response:
                
                if response.status == 200:
                    print(f"Sent message: {content}")
                else:
                    print(f"Failed to send message: {await response.text()}")
