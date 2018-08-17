from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import numpy as np
import glob
import yaml
import subprocess


try:
	subprocess.check_output("ls /home/pi | grep ChessPicss", shell =True)
except subprocess.CalledProcessError:
	subprocess.call("mkdir /home/pi/ChessPicss", shell=True)

def capture(count):

	criteria = (cv2.TERM_CRITERIA_EPS +cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

	objp = np.zeros((6 * 7, 3), np.float32)
	objp[:,:2] = np.mgrid[0:7:,0:6].T.reshape(-1,2)

	camera = PiCamera(resolution = '640x480')
	rawCapture = PiRGBArray(camera, size =(640, 480))

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
			cv2.imwrite("/home/pi/ChessPics/%s" % name, img)

                	objpoints.append(objp)
                	cv2.cornerSubPix(gray, corners, (11,11),(-1,-1), criteria)
                	imgpoints.append(corners)
	               	count += 1

		break

	camera.close()


	return [ret, count]


def calibrate(hostname, ip, frame_id):
	criteria = (cv2.TERM_CRITERIA_EPS +cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)


	objp = np.zeros((6 * 7, 3), np.float32)
	objp[:,:2] = np.mgrid[0:7:,0:6].T.reshape(-1,2)

	objpoints = []
	imgpoints = []

	images = glob.glob('/home/pi/ChessPics/*.png')

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


	data = {"ret": ret, "camera matrix": mtx.tolist(), "distortion coefficients": dist.tolist(), "rotation vectors": rotv, "translation vectors": tranv}

	file = "/home/pi/%s-data.yaml" % hostname


	with open(file, "w") as f:
		yaml.dump(data, f)

	command = "curl -X POST -F \'attributes_str={\"RPi Hostname\": \"%s\", \"Frame ID\": \"%s\", \"file\": \"camera parameters\"}\' -F \"upload=@/home/pi/%s\" %s:7445/node" % (hostname, frame_id,  file, ip)


	subprocess.call(command, shell = True)

