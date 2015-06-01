import subprocess, time, os, logging, re, socket, atexit, glob, itertools, sys, struct
from tprocess import tprocess
from threading import Thread
import sys
from .tserver import tserver

JARS_FOLDER = '/Users/Apple/Documents/datascription/stanford-corenlp-full-2015-01-30/'
SENTIMENT_MODEL = 'edu/stanford/nlp/models/sentiment/sentiment.ser.gz'
PARSER_MODEL = 'edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz'

logging.basicConfig()  
LOG = logging.getLogger("SSPLServer")
LOG.setLevel("INFO")

class SSPLServer(tserver):
	def __init__(self, JARS_FOLDER=JARS_FOLDER, sentiment_model=SENTIMENT_MODEL, parser_model=PARSER_MODEL, server_port=12340, encoding='utf-8'):
		tserver.__init__(self)
		self.encoding = encoding
		self.jars_folder = JARS_FOLDER
		self.output_formats = ['PROBABILITIES']
		self.server_port = server_port
		self.sentiment_model = sentiment_model
		self.parser_model = parser_model
		self.cmd = 'java -cp "*" -Xmx1024m edu.stanford.nlp.sentiment.SentimentPipeline -stdin -output %s -sentimentModel %s -parserModel %s' % (','.join(self.output_formats), self.sentiment_model, self.parser_model)

	def start_server(self):
		LOG.info("Starting SSPL as a subprocess")
		os.chdir( self.jars_folder )
		self.proc = tprocess(self.cmd)
		self.proc.logfile = sys.stdout
		self.proc.expect('Processing will end when EOF is reached.', timeout=None)
		LOG.info(self.proc.before)
		LOG.info("Testing communication with SSPL process")
		output = self.process_text("This is the test sentence on the server. This is the second test sentence from the server.")
		# output = self.proc.before
		#LOG.info(output)
		#LOG.info(type(output))
		output_lines = output.split('\n')
		test_passed = False
		if len(output_lines) > 1:
			test_passed = True
		if not test_passed:
			assert False, "Could not communicate with SSPL subprocess, shutting down..."

		LOG.info("SSPL process started successfully!")

		try:
			self.server_socket = self.get_server_socket()
			self.server_socket.listen(1)
			LOG.info("SSPL Server now listening on port %d" % self.server_port)
			self.server_thread = Thread(target = self.accept_clientes)
			self.server_thread.daemon = True
			self.server_thread.start()
		except Exception as ex:
			assert False, "Could not start the server\n%s" % ex

	def process_text(self, input_text):
		text_processed = ''
		output = ''
		#we introduce a marker to make sure we get all the output from the SSPL
		marker = 'yadayadayada'
		input_text_with_marker = input_text +'\n'+ marker
		self.proc.sendline(input_text_with_marker)
		LOG.info("Expect1...")
		self.proc.expect('\(0 %s\)' % marker , timeout=None)
		output = self.proc.before
		idx = output.find("(0")
		if idx >= 0:
			output = output[idx:]
		LOG.info("This is what I got:\n%s" % output)
		#discard the next few lines
		LOG.info("Expect2...")
		self.proc.expect('\n', timeout=None)
		self.proc.before

		#LOG.info('='*80)
		output = output.replace('\n%s' % marker, '')
		output = output.replace(input_text_with_marker, '')
		#LOG.info(output)
		return output

	def handle_client(self, clientsocket):
		while True:
			input_text = self.receive_text(clientsocket)
			LOG.info("Received '%s' for sentimetn analysis" % input_text)
			output = self.process_text(input_text)
			self.send_text(clientsocket, output)
			LOG.info("Server listening on port %d" % self.server_port)

	def receive_text(self, sock):
		size_info_str = sock.recv(8)
		size_info = struct.unpack('>Q', size_info_str)[0]
		LOG.info(size_info_str)
		LOG.info(size_info)
		chunks = []
		data_chunks = []
		curlen = lambda: sum(len(x) for x in data_chunks)
		while True:
			LOG.info(size_info - curlen())
			data = sock.recv(size_info - curlen())
			data_chunks.append(data)
			chunks.append(data.decode(self.encoding, 'ignore'))
			if curlen() >= size_info: break
			if len(chunks) > 1000:
				LOG.warning("Incomplete value from socket")
				return None
			time.sleep(0.01)
		return ''.join(chunks)

	def send_text(self, sock, text):
		try:
			data = bytes( text + "\n", self.encoding, 'ignore')
		except Exception as e:
			try:
				data = (text + "\n").encode(self.encoding, 'ignore')
			except Exception as ex:
				data = (text + "\n").decode(self.encoding, 'ignore').encode(self.encoding, 'ignore')
		sz = len(data)
		len_info = struct.pack('>Q', sz)
		sock.sendall(len_info)
		sock.sendall( data )

	def get_server_socket(self, num_retries=1, retry_interval=1):
		for i in range(num_retries):
			try:
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.bind(('127.0.0.1', self.server_port))
				return sock
			except Exception as e:
				LOG.info("socket connection could not be made (%s)" % e)
				if i < num_retries-1:
					LOG.info("pausing before retry")
					time.sleep(5)
		assert False, "The socket could not be obtained"


if __name__ == '__main__':

	if len(sys.argv) < 2:
		LOG.info('Usage: %s <port_number> [JARS_FOLDER]' % sys.argv[0])
	else:
		if len(sys.argv) > 2:
			JARS_FOLDER = sys.argv[2]
		port = int(sys.argv[1])
		server = SSPLServer( server_port=port, JARS_FOLDER=JARS_FOLDER )
		server.start_server()
		server.wait_for_command()


