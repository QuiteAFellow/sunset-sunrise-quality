# Sunset / Sunrise quality for any location in the continential United States
A small python program that pulls data from sunsetwx.com and give a sunset/sunrise quality according to the provided GPS Coordinates.

**USAGE**:
```bash
$ python sunset.py sunrise 25.761681, -80.191788
Predicting for GPS coordinates: (25.761681, -80.191788)
sunrise time in zulu: 7Z
The sunset quality is 49%

```

**RUN With docker :)**
```bash
$ docker build -t sunset .
$ docker run -it --rm sunset sunrise 25.761681, -80.191788
Predicting for GPS coordinates: (25.761681, -80.191788)
sunrise time in zulu: 7Z
The sunset quality is 49%
```


## Install
Make sure you have the lib tesseract

**MAC:**
```bash
brew install tesseract
```

**DEBIAN:**
```bash
sudo apt-get install tesseract-ocr
```

**WINDOWS:**
```bash
pip install tesseract-ocr
```


## How does it work?
[Sunsetwx.com](https://sunsetwx.com/view/?id=5) provides a map of the United States every day as an attempt to predict the quality of the sunset for that day.
The closer to an intense red the location is, better quality sunset you can expect. These images are generated very 3 hours according to the NAM Weather model. The validation time is described in ZULU on the top middle of the image, and this time is independent of any position (ZULU Time).

This program parses the sunset/sunrise time for a pre-provided GPS coordinate, downloads every available image for the run of that selected day and selects the best one for the concerned sunset time.
After obtaining the image, it reads a 20 pixel square area around the GPS coordinates and returns the sunset quality percentage according to the scale on the right-hand side of the image.


## Possible future improvements
- Improve algorithms for determining the best image to select for a location before calculating percentage
- Improve adjustments needed for the x,y, coordinates of the image for a provided GPS coordinate
- Find a better way to parse the text of the image
- Improve the algorithms for calculating the sunset quality
- Adjust the current way the script handles someone looking for Sunrise quality
- Wrap the script in a loop so it automatically checks the sunset/sunrise quality at 3pm/9pm respectively
