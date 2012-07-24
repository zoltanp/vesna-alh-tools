import alh
import binascii
import common
import serial
import struct
import time
from optparse import OptionParser, OptionGroup

def upload_firmware(target, firmware, slot_id):
	target.post("prog/nextFirmwareSlotId", "%d" % (slot_id,), "admin")
	target.post("prog/nextFirmwareSize", "%d" % (len(firmware),))
	target.post("prog/nextEraseSlotId", "%d" % (slot_id,))

	chunk_size = 512
	total_size = len(firmware)
	chunk_num = 0
	p = 0
	while p < total_size:
		chunk_data = struct.pack(">i", chunk_num) + firmware[p:p+chunk_size]
		if len(chunk_data) != 516:
			chunk_data += "\xff" * (516 - len(chunk_data))
			
		chunk_data_crc = binascii.crc32(chunk_data)

		chunk = chunk_data + struct.pack(">i", chunk_data_crc)

		target.post("firmware", chunk)

		p += chunk_size
		chunk_num += 1

	target.post("prog/nextFirmwareCrc", "%d" % (binascii.crc32(firmware),))

def reboot_firmware(target, slot_id):
	target.post("prog/setupBootloaderForReprogram", "%d" % (slot_id,))
	target.post("prog/doRestart", "1")

def confirm(target):
	target.post("prog/firstcall", "1")
	target.post("prog/runningFirmwareIsValid", "1")

def main():
	parser = OptionParser(usage="%prog [options]")

	common.add_communication_options(parser)

	parser.add_option("-n", "--node", dest="node", metavar="ADDR", type="int",
			help="Reprogram node with ZigBit address ADDR")
	parser.add_option("-c", "--coordinator", dest="coordinator", action="store_true",
			help="Reprogram coordinator")

	parser.add_option("-i", "--input", dest="input", metavar="PATH",
			help="PATH to firmware to upload")
	parser.add_option("-C", "--confirm", dest="confirm", action="store_true",
			help="Don't reprogram, just confirm currently running firmware as valid")

	parser.add_option("-s", "--slot", dest="slot_id", metavar="ID", type="int", default=1,
			help="Use SD card slot ID for upload")

	(options, args) = parser.parse_args()

	coordinator = common.get_coordinator(options)	
	coordinator.post("prog/firstcall", "1")

	if options.coordinator and not options.node:
		target = coordinator
	elif options.node and not options.coordinator:
		node = alh.ALHProxy(coordinator, options.node)
		node.post("prog/firstcall", "1")
		target = node
	else:
		print "Please give either -n or -c option"
		return -1

	if options.input and not options.confirm:
		firmware = open(options.input).read()
	elif options.confirm and not options.input:
		firmware = None
	else:
		print "Please give either -i or -C option"
		return -1

	if firmware:
		upload_firmware(target, firmware, options.slot_id)

		print "Reprogramming done. Rebooting node."
		reboot_firmware(target, options.slot_id)

		print "Waiting for node to boot."
		time.sleep(60)

	confirm(target)

main()
