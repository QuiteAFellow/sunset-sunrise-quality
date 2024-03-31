from PIL import Image, ImageDraw
import urllib
import urllib.request
from pytesseract import image_to_string
import re
import math
import os
import requests
import pytz
import tzlocal
import ephem
from io import BytesIO
from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder

def Get_Sunset_Quality(lat:float, lon:float, Sunset:bool):

    URL_BASE = "https://sunsetwx.com/sunrise/sunrise_f"
    IMAGE_DATA = {
        'xa': 63,
        'xb': 1336,
        'ya': 196,
        'yb': 833
    }

    PALETTE = {
        'xa': 1348,
        'xb': 1348,
        'ya': 197,
        'yb': 886
    }

    UP_IMAGE_LAT = 50.67
    DOWN_IMAGE_LAT = 23.3

    LEFT_IMAGE_LON = -125.4
    RIGHT_IMAGE_LON = -65.0

    lon_coeff = 1.0105

    GPS_COORDS_TO_CHECK = (lat, lon)

    #Common Cities to test for reference:
    #New York City 	40.71427, -74.00597
    #Los Angeles 	34.05223, -118.24368
    #Chicago 	41.85003, -87.65005
    #Houston 	29.76328, -95.36327
    #Philadelphia 	39.95233, -75.16379
    #Phoenix 	33.44838, -112.07404
    #San Antonio 	29.42412, -98.49363
    #San Diego 	32.71571, -117.16472
    #Dallas 	32.78306, -96.80667
    #Brooklyn 	40.6501, -73.94958
    #Queens 	40.68149, -73.83652
    #San Jose 	37.33939, -121.89496
    #Austin 	30.26715, -97.74306
    #Jacksonville 	30.33218, -81.65565
    #San Francisco 	37.77493, -122.41942
    #Columbus 	39.96118, -82.99879
    #Fort Worth 	32.72541, -97.32085
    #Indianapolis 	39.76838, -86.15804
    #Charlotte 	35.22709, -80.84313
    #Manhattan 	40.78343, -73.96625
    #Miami 25.761681, -80.191788
    #Tampa 27.964157, -82.452606
    #Limestone(Maine) 46.91141695449645, -67.82556040331153

    if bool(Sunset):
        URL_BASE = URL_BASE.replace("sunrise", "sunset")

    def refine_number(str):
        return str.replace("O", "0").replace("o", "0").replace("B", "6").replace("Q", "9")

    def get_pixelxy_per_cood(lat, lon):
        lat_dist_ref = lat - UP_IMAGE_LAT
        lat_max_dist = DOWN_IMAGE_LAT - UP_IMAGE_LAT
        lat_percentage = lat_dist_ref / lat_max_dist
        if lat_percentage < 0 or lat_percentage > 100:
            print('latitude not supported')
            exit(1)

        lon_dist_ref = lon - LEFT_IMAGE_LON
        lon_max_dist = RIGHT_IMAGE_LON - LEFT_IMAGE_LON
        lon_percentage = lon_dist_ref / lon_max_dist
        lon_percentage_adj = lon_percentage * lon_coeff
        if lon_percentage < 0 or lon_percentage > 100:
            print('longitude not supported')
            exit(1)

        x_length = IMAGE_DATA['xb'] - IMAGE_DATA['xa']
        x = int(IMAGE_DATA['xa'] + x_length * lon_percentage_adj)

        y_length = IMAGE_DATA['yb'] - IMAGE_DATA['ya']
        y = int(IMAGE_DATA['ya'] + y_length * lat_percentage)
        y_adj = int(((2 / 17) * y ** 0.1) + ((1 / 10) * y ** 1.1) - ((1 / 23) * y ** 1.12) + y)
        return x, y_adj

    def distanceRGB(c1, c2):
        (r1, g1, b1) = c1
        (r2, g2, b2) = c2
        return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)

    # Define a temporary directory to store the images
    TEMP_DIR = "D:\Coding Projects\Sunsetwx Discord Bot\Github\dir_temp"

    def extract_text(img_data):
        # Create the temporary directory if it doesn't exist
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)

        img = Image.open(img_data)

        myText = image_to_string(img,lang='eng')
        img.close

        #print("Extracted Text: ", myText)

        # Define regex pattern to match time in the format HH:MM
        time_pattern = r'\| (\d{1,2}:\d{2}) ET \|'
        time_of_validity = re.search(time_pattern, myText)

        # If time is found, refine and return it
        if time_of_validity:
            time_of_validity = refine_number(time_of_validity.group(1))
        else:
            # If time is not found, return None
            time_of_validity = None

        #print('Time of validity:', time_of_validity)
        return time_of_validity

    def get_sunset_quality(image_url):
        urllib.request.urlretrieve(image_url, "image.png")
        image = Image.open("image.png")
        pix = image.load()

        PALETE_DIC = {}
        for i in range(0, PALETTE['yb'] - PALETTE['ya']):
            cur_percent = (1.00 - float(i) / float(PALETTE['yb'] - PALETTE['ya'])) * 100
            cur_rgb = pix[PALETTE['xa'], PALETTE['ya'] + i]
            PALETE_DIC[cur_rgb] = cur_percent

        x, y = get_pixelxy_per_cood(GPS_COORDS_TO_CHECK[0], GPS_COORDS_TO_CHECK[1])
        SIZE_SAMPLE = 10
        sample_around_coords = image.crop((x - SIZE_SAMPLE, y - SIZE_SAMPLE, x + SIZE_SAMPLE, y + SIZE_SAMPLE))
        sample_around_coords_pix = sample_around_coords.load()

        DARK_PIXEL = 60
        pixels = []
        for x in range(0, sample_around_coords.size[0]):
            for y in range(0, sample_around_coords.size[1]):
                cur_pixel = sample_around_coords_pix[x, y]
                if not (cur_pixel[0] < DARK_PIXEL and cur_pixel[1] < DARK_PIXEL and cur_pixel[2] < DARK_PIXEL):
                    pixels.append(cur_pixel)

        sum_rgb = tuple([sum(el) for el in zip(*pixels)])
        average_color_sample = tuple([x / len(pixels) for x in sum_rgb])

        colors = list(PALETE_DIC.keys())
        closest_colors = sorted(colors, key=lambda color: distanceRGB(color, average_color_sample))
        closest_color = closest_colors[0]

        return int(PALETE_DIC[closest_color])

    def create_cropped_image(image):
        # Get the coordinates for the center point
        x_center, y_center = get_pixelxy_per_cood(GPS_COORDS_TO_CHECK[0], GPS_COORDS_TO_CHECK[1])

        # Calculate the bounding box for cropping
        crop_size = 100
        left = x_center - crop_size // 2
        upper = y_center - crop_size // 2
        right = x_center + crop_size // 2
        lower = y_center + crop_size // 2

        # Crop the image
        cropped_img = image.crop((left, upper, right, lower))

        # Draw a hot pink dot with a black outline at the center
        draw = ImageDraw.Draw(cropped_img)
        dot_center = (crop_size // 2, crop_size // 2)
        dot_radius = 1
        draw.ellipse(
            (dot_center[0] - dot_radius,
            dot_center[1] - dot_radius,
            dot_center[0] + dot_radius,
            dot_center[1] + dot_radius),
            fill='hotpink', outline='black'
        )

        return cropped_img

    def calculate_golden_hour(latitude, longitude, sunset):
        # Assume today's date
        date = datetime.now()

        obs = ephem.Observer()
        obs.lat = str(latitude)
        obs.long = str(longitude)
        obs.date = date

        sun = ephem.Sun(obs)

        if sunset:
        # Calculate sunset time
            sunset_time = obs.next_setting(sun)
        else:
        # Calculate sunrise time
            sunset_time = obs.next_rising(sun)

        # Convert sunset time to local time zone
        local_tz = pytz.timezone(tf.timezone_at(lat=latitude, lng=longitude))
        sunset_local = sunset_time.datetime().replace(tzinfo=pytz.utc).astimezone(local_tz)

        if sunset:
                golden_hour_start = sunset_local - timedelta(hours=2)  # Two hours before sunset
                golden_hour_end = sunset_local + timedelta(hours=1)    # One hour after sunset
        else:
            golden_hour_start = sunset_local - timedelta(hours=1)  # One hour before sunrise
            golden_hour_end = sunset_local + timedelta(hours=2)    # Two hours after sunrise

        golden_hour_start_local = golden_hour_start.replace(year=1900, month=1, day=1)
        golden_hour_end_local = golden_hour_end.replace(year=1900, month=1, day=1)

        #print("Golden Hour Start (local time):", golden_hour_start_local)
        #print("Golden Hour End (local time):", golden_hour_end_local)

        return golden_hour_start_local, golden_hour_end_local

    #def is_within_golden_hour(latitude, longitude, date_time):
        #golden_hour_start, golden_hour_end = get_golden_hour_times(latitude, longitude, date_time)

        # Check if the given date_time is within the golden hour
        #return golden_hour_start <= date_time <= golden_hour_end

    def find_best_sunset_image(sunset):
        best_quality_within_golden_hour = -1
        best_image_within_golden_hour = ""
        best_sunset_initialization_within_golden_hour = ""

        # Get the golden hour times
        if sunset:
            golden_hour_start, golden_hour_end = calculate_golden_hour(GPS_COORDS_TO_CHECK[0], GPS_COORDS_TO_CHECK[1], sunset)
        else:
            golden_hour_start, golden_hour_end = calculate_golden_hour(GPS_COORDS_TO_CHECK[0], GPS_COORDS_TO_CHECK[1], sunset)


        # Loop through the images
        for i in range(2, 16):
            image_url = f"{URL_BASE}{i}.png"

            # Download the image into memory
            response = requests.get(image_url)

            # Extract initialization time from the image
            best_sunset_initialization = extract_text(BytesIO(response.content))
            #print("Best sunset initialization time is: ", best_sunset_initialization)
            # Convert the initialization time to a datetime object
            sunset_time = datetime.strptime(best_sunset_initialization, '%H:%M')
            #print(f"Sunset time for image_{i}: ", sunset_time)
            # Check if the sunset initialization time falls within the golden hour
            if golden_hour_start.time().replace(second=0, microsecond=0) <= sunset_time.time().replace(second=0, microsecond=0) <= golden_hour_end.time().replace(second=0, microsecond=0):
                # Get sunset quality
                sunset_quality = get_sunset_quality(image_url)
                #print("Sunset Quality: ", sunset_quality, "%")
                # Update best sunset quality within golden hour
                if sunset_quality > best_quality_within_golden_hour:
                    best_quality_within_golden_hour = sunset_quality
                    best_image_within_golden_hour = response.content
                    best_sunset_initialization_within_golden_hour = sunset_time
                    #print("Best Sunset Quality: ", best_quality_within_golden_hour)

        # Check if any image with valid sunset initialization time was found within the golden hour
        if best_quality_within_golden_hour > -1:
            # Save the best image to a file
            best_image_path = f"{TEMP_DIR}best_sunset_image.png"
            with open(best_image_path, 'wb') as f:
                f.write(best_image_within_golden_hour)

            # Get the local timezone
            local_timezone = tzlocal.get_localzone()

            # Convert the best sunset initialization time to the local timezone
            sunset_time_local = best_sunset_initialization_within_golden_hour.replace(tzinfo=pytz.timezone('US/Eastern')).astimezone(local_timezone)

            # Format the adjusted time as 12-hour time with AM/PM
            sunset_time_local_12hr_adjusted = sunset_time_local.strftime('%I:%M %p')

            # Create an image object from the saved image
            img = Image.open(best_image_path)

            # Create a cropped image with the pink star
            cropped_img = create_cropped_image(img)

            # Save or display the cropped image as needed
            cropped_img.show()

            return print(f"Best sunset quality within Golden Hour: {best_quality_within_golden_hour}% at {sunset_time_local_12hr_adjusted}")
        else:
            return print("Could not find a sunset prediction with valid initialization time within today's Golden Hour.")
    find_best_sunset_image(sunset)

if __name__ =="__main__":
    lat = float(input("Enter latitude: "))
    lon = float(input("Enter longitude: "))
    sunset_input = input("Find sunset percentage(True), or Sunrise percentage? (leave empty): ")
    sunset = sunset_input.lower() == "true"

    tf = TimezoneFinder()

    Get_Sunset_Quality(lat, lon, sunset)