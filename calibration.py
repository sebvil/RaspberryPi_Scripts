from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import numpy as np
import glob
import yaml
import subprocess

def capture(count):

	criteria = (cv2.TERM_CRITERIA_EPS +cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

	objp = np.zeros((6 * 7, 3), np.float32)
	objp[:,:2] = np.mgrid[0:7:,0:6].T.reshape(-1,2)

	camera = PiCamera(resolution = '960x720')
	rawCapture = PiRGBArray(camera, size =(960, 720))

	objpoints = []
	imgpoints = []

	time.sleep(1)


	for frame  in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):

		image = frame.array
		img = image
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

		ret, corners = cv2.findChessboardCorners(gray, (7 ,6), None)




		if ret == True:
			name = "%i.png" % count

			cv2.imwrite("Chess1/%s" % name, img)

                	objpoints.append(objp)
                	cv2.cornerSubPix(gray, corners, (11,11),(-1,-1), criteria)
                	imgpoints.append(corners)
	               	count += 1

		break

	camera.close()


	return [ret, count]


def calibrate(hostname):
	criteria = (cv2.TERM_CRITERIA_EPS +cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)


	objp = np.zeros((6 * 7, 3), np.float32)
	objp[:,:2] = np.mgrid[0:7:,0:6].T.reshape(-1,2)

	objpoints = []
	imgpoints = []

	images = glob.glob('Chess1/*.png')

	for fname in images:
        	img = cv2.imread(fname)
        	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        	ret, corners = cv2.findChessboardCorners(gray, (7, 6), None)

        	if ret == True:
                	objpoints.append(objp)
                	cv2.cornerSubPix(gray, corners, (11,11),(-1,-1), criteria)
                	imgpoints.append(corners)


	ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

	rotv = []
	tranv= []
	for arr in rvecs:

		rotv.append(arr.tolist())
	for arr in tvecs:
		tranv.append(arr.tolist())


	data = {"ret": ret, "camera _matrix": mtx.tolist(), "distortion coefficients": dist.tolist(), "rotation vectors": rotv, "translation vectors": tranv}

	file = "camera_data.yaml"


	with open(file, "w") as f:
		yaml.dump(data, f)

	ip = subprocess.check_output("/home/pi/'Camera Project'/getIP.sh", shell =True).strip()

	command = "curl -X POST -F \'attributes_str={\"RPi Hostname\": \"%s\", \"file\": \"camera parameters\"}\' -F \"upload=@camera_data.yaml\" %s:7445/node" % (hostname, ip)

	subprocess.call(command, shell = True)