from alh import alh
from alh.spectrum import *
from alh.common import log
import os
import serial
import string
import sys
import time
import pickle

def test_tx(time_start_arg,
			nodef,
			tx_node_nr,
			rx_number_list
			):
	# cognitive terminal, default frequency
	SignalGenerationRun(
			alh = nodef(tx_node_nr),
			time_start = time_start_arg + 5.0,
			time_duration = 25,
			device_id = 0,
			config_id = 0,
			channel = 110,
			power = 0).program()

	# cognitive terminal, moved frequency
	SignalGenerationRun(
			alh = nodef(tx_node_nr),
			time_start = time_start_arg + 35.0,
			time_duration = 20,
			device_id = 0,
			config_id = 0,
			channel = 225,
			power = 0).program()

	rx_nodes = []
	for rx_nr in rx_number_list:
		rx_nodes.append( nodef(rx_nr))

	return MultiNodeSpectrumSensingRun(
			nodes = rx_nodes,
			time_start = time_start_arg,
			time_duration = 60,
			device_id = 0,
			config_id = 0,
			ch_start = 0,
			ch_step = 1,
			ch_stop = 255,
			slot_id = 6)

	# TODO if the automatic authentication loading is merged, remove this function
def load_auth():
	try:
		f = open("thesis-sensing-auth.pickle", "r")
	except IOError:
		print "authentication file open error"
		return [ "", "" ]
	pwd_pass_dict = pickle.load(f)
	f.close()
	return [pwd_pass_dict['user'], pwd_pass_dict['pwd']]


def main():
	#f = serial.Serial("/dev/ttyUSB0", 115200, timeout=10)
	#coor = alh.ALHTerminal(f)

	[user, pwd] = load_auth()

	coor = alh.ALHWeb("https://%s:%s@crn.log-a-tec.eu/communicator" % ( user, pwd),
					10001)
	coor._log = log

	called = set()

	def nodef(addr):
		n = alh.ALHProxy(coor, addr)

		if addr not in called:
			n.post("prog/firstCall", "1")
			called.add(addr)

		return n

	extra_wait = 80

	node_numbers = [ 2, 4, 6, 11, 13, 15, 17, 24, 25, 26 ]

	for tx_node_nr in node_numbers:

		print "tx_node_nr = ", tx_node_nr

		# copy the list
		rx_number_list = list(node_numbers)
		rx_number_list.remove(tx_node_nr)


		time_start = time.time() + extra_wait

		experiment = test_tx(
							time_start_arg=time_start,
							nodef=nodef,
							tx_node_nr=tx_node_nr,
							rx_number_list=rx_number_list)

		experiment.program()

		print "waiting %d s so the experiment can finish" % (60 + extra_wait)
		time.sleep(60 + extra_wait);

		while not experiment.is_complete():
			print "waiting..."
			time.sleep(2)

		print "experiment is finished. retrieving data."

		results = experiment.retrieve()

		output_dirname = "data-%d-tx" % (tx_node_nr)
		for rx_nr in rx_number_list:
			output_dirname = output_dirname + "-" + str(rx_nr)
		output_dirname = output_dirname + "-rx"

		try:
			os.mkdir(output_dirname)
		except OSError:
			pass
		write_results(output_dirname, results, experiment)

		print "done, waiting 5s"
		time.sleep(5)

main()
