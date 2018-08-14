import pika
import subprocess
import picamera
import datetime
import shlex
import calibration

hostname = subprocess.check_output("hostname", shell=True).strip()

commander_hostname = "sebastian-VirtualBox"

credentials = pika.PlainCredentials('sebvil1', 'rabbit')

ip = subprocess.check_output("avahi-resolve-host-name %s.local" % commander_hostname, shell = True).split()[1]

ip = ip+"%eth0"

parameters = pika.ConnectionParameters(ip, 5672, "/", credentials)
connection = pika.BlockingConnection(parameters)

channel = connection.channel()

channel.exchange_declare(exchange='commands', exchange_type='direct', durable = True)
channel.exchange_declare(exchange='confirmation', durable=True)
channel.queue_declare(queue = hostname, exclusive=True)
channel.queue_bind(exchange='commands', queue=hostname)

response = ""
frame_id = ""
def callback(ch, method, props, body):
	global response
	global frame_id
	print "Received command: %s" % body
	channel.stop_consuming()
	response =  body
	frame_id = props.correlation_id
def take_picture(cam, filename):
	cam.capture(filename)								# Takes picture and saves it under the filename

def send_to_shock(image, frame_id, ip):
	time = str(datetime.datetime.now())                                             # Gets current time
	# Command ends picture along with metadata to shock-server
	command = "curl -X POST -F \'attributes_str={\"Frame ID\": \"%s\", \"RPi Hostname\": \"%s\", \"Time Stamp\": \"%s\", \"Image name\" :\"%s\"}\' -F \"upload=@%s\" %s:7445/node" % (frame_id, hostname, time, image, image, ip)

	args = shlex.split(command)							# Splits the words of the command and puts it in a list. Necessarry fo subprocess.call method below
	try:
		out = subprocess.check_output(args)
		start = out.find("id")+5
		end = out.find('","ver')
		id = out[start:end]
		return ["Picture sent succesfully", id]
	except subprocess.CalledProcessError:
		return ["Picture could not be sent", "None"]							# Calls the command, i.e., sends picture shock-server
	print " "

count = 0
trials = 0
while True:
	quit = False
	print "Waiting for command..."
	channel.basic_consume(callback, queue=hostname, no_ack=True)
	channel.start_consuming()

	message = ""
	id = "None"
	if response == "1":
		print "Command received: Take picture and send it to Shock."
		camera = picamera.PiCamera(resolution='3280x2464')
		take_picture(camera, "image.jpg")
		resp = send_to_shock("image.jpg", frame_id, ip)
		message = resp[0]
		id = resp[1]
		camera.close()
	elif response == "2":
		print "Command received: Quit"
		quit = True
		message = "Quit succesfully"
		break
	elif response == "3":
		print "Command received: Calibrate camera"
		if count < 10:
			subprocess.call("mkdir ../ChessPics")
			ret, count = calibration.capture(count)
			trials += 1
		        channel.basic_publish(exchange='confirmation', routing_key='confirmation', properties=pika.BasicProperties(reply_to=hostname, correlation_id = id), body = "Picture taken: %r  Successes/Trials: %s/%s" % (ret, count, trials) )
			continue
		print "count =", count
		if count == 10:
			count = 0
			trials =0 
			calibration.calibrate(hostname, ip)
			message = "calibrated"
	elif response == "4":
		print "Command received: Restart calibration"
		count = 0
		trials = 0
		message = "Calibration reset"
	else:
		message=  "Command '%s' not found" % response
		print message

	channel.basic_publish(exchange='confirmation', routing_key='confirmation', properties=pika.BasicProperties(reply_to=hostname, correlation_id = id), body = message) 

channel.basic_publish(exchange='confirmation', routing_key='confirmation', properties=pika.BasicProperties(reply_to=hostname), body=message)

connection.close()

