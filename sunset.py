#code pulled from https://github.com/markthebault/sunset-sunrise-quality/blob/master/sunset.py

#!/bin/python
from PIL import Image
import urllib
from urllib.request import urlretrieve
from pytesseract import image_to_string
import pytesseract
import re
import math
import ephem
import sys

#/ ! \ Make sure you have tesseract-ocr

URL_BASE = "https://sunsetwx.com/sunset/sunset_f"
#pytesseract.pytesseract.tesseract_cmd = "C:\Program Files\Tesseract-OCR\tesseract.exe"
IMAGE_DATA = {
    'xa' : 63,
    'xb' : 1336,
    'ya' : 196,
    'yb' : 833
}

PALETTE = {
    'xa' : 1348,
    'xb' : 1348,
    'ya' : 197,
    'yb' : 886
}

UP_IMAGE_LAT = 50.67
DOWN_IMAGE_LAT =  23.3

LEFT_IMAGE_LON = -125.4
RIGHT_IMAGE_LON = -65.0

TIME_BETWEEN_UPDATES = 3

lat_coeff = 1
lon_coeff = 1.0105

GPS_COORDS_TO_CHECK = (25.761681, -80.191788)

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

#This will be changed with user desired value
#Currently set to Charlotte

CHECK_FOR_SUNSET = True #if set to false that means sunrise check

if CHECK_FOR_SUNSET:
    URL_BASE = URL_BASE.replace("sunrise", "sunset")


#GET the latittude and longitude from the parameters
if len(sys.argv) != 4:
    print ("HELP: "+sys.argv[0]+" [sunset | sunrise] [LATITTUDE] [LONGITUDE]")
    print ("Example: "+sys.argv[0]+" sunset 35.12278364940427, -80.87630505622226")
    print ("By default Charlotte, NC coordinates will be considered for sunset")
else:
    CHECK_FOR_SUNSET = sys.argv[1].lower() == "sunset"
    GPS_COORDS_TO_CHECK = (float(sys.argv[2]), float(sys.argv[3]))


print ("Predicting for GPS coordinates: "+str(GPS_COORDS_TO_CHECK))

#GET SUNSET TIME
home = ephem.Observer()
home.lat = str(GPS_COORDS_TO_CHECK[0])
home.lon = str(GPS_COORDS_TO_CHECK[1])
sun = ephem.Sun()
sun.compute(home)
sun_cross_date = home.next_setting(sun) if CHECK_FOR_SUNSET else home.next_rising(sun)
sun_crossing_horizon_time_zulu = sun_cross_date.datetime().hour + (1 if sun_cross_date.datetime().minute > 30 else 0)

print ("sunset"+" time in zulu: "+str(sun_crossing_horizon_time_zulu) + "Z") if CHECK_FOR_SUNSET else print("sunrise"+" time in zulu: "+str(sun_crossing_horizon_time_zulu) + "Z")



def refine_number(str):
    return str.replace("O", "0").replace("o", "0").replace("B","6").replace("Q","9")
#Get the right image to use
distance = 1000;
image_to_use = ""

for id in range(2,11):
    url_curr_image=URL_BASE+str(id)+'.png'
    image_name="prediction"+str(id)+".png"

    #Get the image
    urllib.request.urlretrieve(url_curr_image, image_name)

    #GET the text of the image to extract the date
    myText = image_to_string(Image.open(image_name), lang='eng')

    search_result = re.search(', ([A-Z]{3}) (\d\d) (\d\d\d\d)', myText)
    time_of_validity = {}
    if search_result:
        time_of_validity['day'] = search_result.group(2)
        time_of_validity['month'] = search_result.group(1)
        time_of_validity['year'] = search_result.group(3)

    hour_of_validity = re.search('Valid at: (..)', myText)
    hour_of_validity = refine_number(hour_of_validity.group(1)) if hour_of_validity else -1
    hour_of_validity = int(hour_of_validity)
    if distance > abs(hour_of_validity - sun_crossing_horizon_time_zulu):
        distance = abs(hour_of_validity - sun_crossing_horizon_time_zulu)
        image_to_use = image_name

    #print 'hour of validity:'+str(hour_of_validity)
    #print time_of_validity


#print image_to_use

image = Image.open(image_to_use)
pix = image.load()


#Get the palette colors
PALETE_DIC = {}
for i in range(0,PALETTE['yb']-PALETTE['ya']):
    cur_percent = (1.00 - float(i) / float(PALETTE['yb']-PALETTE['ya']))*100
    cur_rgb = pix[PALETTE['xa'],PALETTE['ya']+i]
    PALETE_DIC[cur_rgb] = cur_percent


def get_pixelxy_per_cood(lat, lon):
    lat_dist_ref = lat - UP_IMAGE_LAT;
    lat_max_dist = DOWN_IMAGE_LAT - UP_IMAGE_LAT;
    lat_percentage = lat_dist_ref / lat_max_dist
    if lat_percentage < 0 or lat_percentage > 100:
        print ('latitude not suported')
        exit(1);

    lon_dist_ref = lon - LEFT_IMAGE_LON;
    lon_max_dist = RIGHT_IMAGE_LON - LEFT_IMAGE_LON;
    lon_percentage = lon_dist_ref / lon_max_dist
    lon_percentage_adj = lon_percentage*1.0105
    if lon_percentage < 0 or lon_percentage > 100:
        print ('longitude not suported')
        exit(1);

    x_length = IMAGE_DATA['xb'] - IMAGE_DATA['xa']
    x = int(IMAGE_DATA['xa'] + x_length * lon_percentage_adj)

    y_length = IMAGE_DATA['yb'] - IMAGE_DATA['ya']
    y = int(IMAGE_DATA['ya'] + y_length * lat_percentage)
    y_adj = int(((2/17)*y**0.1)+((1/10)*y**1.1)-((1/23)*y**1.12)+y)
    return x,y_adj

def getAverageRGB(image):
  """
  Given PIL Image, return average value of color as (r, g, b)
  """
  # no. of pixels in image
  npixels = image.size[0]*image.size[1]
  # get colors as [(cnt1, (r1, g1, b1)), ...]
  cols = image.getcolors(npixels)
  # get [(c1*r1, c1*g1, c1*g2),...]
  sumRGB = [(x[0]*x[1][0], x[0]*x[1][1], x[0]*x[1][2]) for x in cols]
  # calculate (sum(ci*ri)/np, sum(ci*gi)/np, sum(ci*bi)/np)
  # the zip gives us [(c1*r1, c2*r2, ..), (c1*g1, c1*g2,...)...]
  avg = tuple([sum(x)/npixels for x in zip(*sumRGB)])
  return avg

def distanceRGB(c1, c2):
    (r1,g1,b1) = c1
    (r2,g2,b2) = c2
    return math.sqrt((r1 - r2)**2 + (g1 - g2) ** 2 + (b1 - b2) **2)



x,y = get_pixelxy_per_cood(GPS_COORDS_TO_CHECK[0],GPS_COORDS_TO_CHECK[1])
SIZE_SAMPLE = 10
sample_around_coords = image.crop((x-SIZE_SAMPLE,y-SIZE_SAMPLE,x+SIZE_SAMPLE,y+SIZE_SAMPLE))
sample_around_coords.save('result.png')
sample_around_coords_pix = sample_around_coords.load()

#Average color in the sample without including dark pixels
DARK_PIXEL = 60
color_avg = (0,0,0)
pixels = []
for x in range(0,sample_around_coords.size[0]):
    for y in range(0,sample_around_coords.size[1]):
        cur_pixel = sample_around_coords_pix[x,y]
        if not(cur_pixel[0] < DARK_PIXEL and cur_pixel[1] < DARK_PIXEL and cur_pixel[2] < DARK_PIXEL):
            pixels.append(cur_pixel)

sum_rgb = tuple([sum(el) for el in zip(*pixels)])
average_color_sample = tuple([x/len(pixels) for x in sum_rgb])


#Get the closest color close to the average
colors = list(PALETE_DIC.keys())
closest_colors = sorted(colors, key=lambda color: distanceRGB(color, average_color_sample))
closest_color = closest_colors[0]
print('The sunset quality is ' +str(int(PALETE_DIC[closest_color]))+'%')


#print image.size
#print pix[100,100]