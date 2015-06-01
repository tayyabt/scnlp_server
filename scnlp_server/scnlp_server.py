import subprocess, time, os, logging, re, socket, atexit, glob, itertools, sys, struct
from tprocess import tprocess
from threading import Thread
import sys
import math
from .tserver import tserver

JARS_FOLDER = '/Users/Apple/Documents/datascription/stanford-corenlp-full-2015-01-30/'

logging.basicConfig()  
LOG = logging.getLogger("SCNLPServer")
LOG.setLevel("INFO")

class SCNLPServer(tserver):
	def __init__(self, JARS_FOLDER=JARS_FOLDER, server_port=12340, annotators='tokenize,ssplit,pos,lemma,ner,parse,dcoref', memory='8g', options=None, encoding='utf-8'):
		tserver.__init__(self)
		self.encoding = encoding
		self.jars_folder = JARS_FOLDER
		self.server_port = server_port
		self.annotators = annotators
		self.stop_server = False
		#java -cp "*" -Xmx4g edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma,ner,parse,dcoref -outputFormat xml
		self.cmd = 'java -cp "*" -Xmx%s edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators %s -outputFormat xml' % (memory, self.annotators)
		if options:
			self.cmd = '%s %s' % (self.cmd, options)

	def start_server(self):
		self.stop_server = False
		LOG.info("Starting SCNLP as a subprocess")
		os.chdir( self.jars_folder )
		LOG.info("Starting with command:\n%s" % self.cmd)
		self.proc = tprocess(self.cmd)
		#self.proc.logfile = sys.stdout
		self.proc.expect('NLP>', timeout=None)
		LOG.info(self.proc.before)
		LOG.info("Testing communication with SCNLP process")
		output = self.process_text("This is the test sentence on the server. This is the second test sentence from the server.")
		output_lines = output.split('\n')
		self.server_thread = None
		test_passed = False
		if len(output_lines) > 1:
			test_passed = True
		if not test_passed:
			assert False, "Could not communicate with SCNLP subprocess, shutting down..."

		LOG.info("SCNLP process started successfully!")

		try:
			self.server_socket = self.get_server_socket()
			self.server_socket.listen(1)
			LOG.info("SCNLP Server now listening on port %d" % self.server_port)
			self.server_thread = Thread(target = self.accept_clientes)
			self.server_thread.daemon = True
			self.server_thread.start()
		except Exception as ex:
			assert False, "Could not start the server\n%s" % ex
		print("Returning from the start_server method")
		return 1

	def process_text(self, input_text):
		input_text = re.sub( '\\r', '', input_text )
		input_text = re.sub( '\.(\\n)+', '.', input_text )
		input_text = re.sub( '^(\\n)+ *', '', input_text )
		input_text = re.sub( '(\\n)+ ', '. ', input_text )
		input_text = re.sub( '(\\n)+', '', input_text )
		text_processed = ''
		output = ''
		# if len(input_text) > 1023:
		# 	for i in range(0, math.ceil( len(input_text)/1024.0 )):
		# 		self.proc.send( input_text[ i*1024 : min( len(input_text), (i+1)*1024 ) ] )
		# 	self.proc.sendline()
		# else:
		self.proc.sendline(input_text)
		while True:
			self.proc.expect('NLP>', timeout=None)
			output = output + self.proc.before
			#LOG.info("got some output")
			#LOG.info(output)
			if output.find("<") >= 0:
				break
		
		xml_start = output.find("<")
		output = output[xml_start:]
		output = output.strip()

		LOG.info("Returning output: \n%s" % output)
		return output

	def handle_client(self, clientsocket):
		while True:
			try:
				input_text = self.receive_text(clientsocket)
				LOG.info("Received '%s' for analysis" % input_text)
				output = self.process_text(input_text)
				self.send_text(clientsocket, output)
				LOG.info("Server with annotators %s listening on %d" % (self.annotators, self.server_port))
			except Exception as ex:
				LOG.info("An exception occured while handling a client.\n%s" % ex)
				clientsocket.close()
				break

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
			#time.sleep(0.01)
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
	

	def __del__(self):
		LOG.info("Winding down the server")
		self.server_socket.close()
		LOG.info("Winding down the child process")
		self.proc = None
		LOG.info("closed the child process and port")



if __name__ == '__main__':

	if len(sys.argv) < 2:
		LOG.info('Usage: %s <port_number> [annotators] [JARS_FOLDER]' % sys.argv[0])
	else:
		annotators = 'tokenize,ssplit,pos,lemma,ner,parse,dcoref'
		if len(sys.argv) > 3:
			JARS_FOLDER = sys.argv[3]
		port = int(sys.argv[1])
		if len(sys.argv) > 2:
			annotators = sys.argv[2]
		server = SCNLPServer( server_port=port, JARS_FOLDER=JARS_FOLDER, annotators=annotators )
		
		ret = server.start_server()
		server.wait_for_command()