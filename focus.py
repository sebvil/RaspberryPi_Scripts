from picamera import PiCamera
from time import sleep


camera = PiCamera()
try:
	camera.start_preview(alpha=255)
	print('before...')
	sleep(300)
	print('...after')
finally:
	print('FINALLY')
	camera.stop_preview()
	camera.close()
	print('END')

