import socket, sys, struct
import logging
from nltk.tree import ParentedTree
import re
import math
from xml2json import xml2json
from optparse import OptionParser
import json
import time

logging.basicConfig()  
LOG = logging.getLogger("SCNLPClient")
LOG.setLevel("INFO")

g_lines = []

class SCNLPClient:
	def __init__(self, server_port):
		self.server_port = server_port
		
	def connect_to_server(self, num_retries=1, retry_interval=1):
		for i in range(num_retries):
			try:
				LOG.info("Connecting to SCNLP server on port %d" % self.server_port)
				self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.sock.connect(('127.0.0.1', self.server_port))
				LOG.info("Connected to server, testing connection...")
				output = self.process_text("Hello World")
				LOG.info("Successfully tested connection")
				return
			except Exception as e:
				LOG.info("socket connection could not be made (%s)" % e)
				if i < num_retries-1:
					LOG.info("pausing before retry")
					time.sleep(5)
		assert False, "The socket could not be obtained"

	def process_text(self, text, convert_to_json=True):
		try:
			self.send_text(text)
			output = self.receive_text()
			output = re.sub('\r', '', output)
			output = re.sub('\n', '', output)
			if convert_to_json:
				parser = OptionParser()
				parser.add_option("-p", "--pretty", default=True)
				(options, args) = parser.parse_args()
				output = xml2json(output, options)
				output = json.loads(output)
			return output
		except Exception as ex:
			LOG.info("An exception occured while processing.\n%s" % ex)
			return None


	def receive_text(self):
		size_info_str = self.sock.recv(8)
		size_info = struct.unpack('>Q', size_info_str)[0]

		chunks = []
		curlen = lambda: sum(len(x) for x in chunks)
		while True:
			data = self.sock.recv(size_info - curlen())
			chunks.append(data.decode('ascii', 'ignore'))
			if curlen() >= size_info: break
			if len(chunks) > 1000:
				LOG.warning("Incomplete value from socket")
				return None
			#time.sleep(0.01)
		return ''.join(chunks)

	def send_text(self, text):
		data = bytes( text + "\n", 'ascii', 'ignore')
		sz = len(data)
		len_info = struct.pack('>Q', sz)
		self.sock.sendall(len_info)
		self.sock.sendall( data )


	def close(self):
		self.sock.close()


if __name__ == '__main__':
	port = int(sys.argv[1])
	scnlp_client = SCNLPClient(port)
	scnlp_client.connect_to_server()
	# LOG.info("Enter 'quit' to quit")
	# while True:
	# 	input = sys.stdin.readline()
	# 	if input.strip() == 'quit':
	# 		break
	# 	output = scnlp_client.process_text(input)
	# 	LOG.info( output )
	# 	LOG.info("")
	# scnlp_client.close()
	