import socket, sys, struct
import logging
from nltk.tree import ParentedTree
import re
import math

logging.basicConfig()  
LOG = logging.getLogger("SSPLClient")
LOG.setLevel("INFO")

g_lines = []

class SSPLClient:
	def __init__(self, server_port, encoding='utf-8'):
		self.server_port = server_port
		self.encoding = encoding
		


	def connect_to_server(self, num_retries=1, retry_interval=1):
		for i in range(num_retries):
			try:
				LOG.info("Connecting to SSPL server on port %d" % self.server_port)
				self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.sock.connect(('127.0.0.1', self.server_port))
				LOG.info("Connected to server, testing connection...")
				output = self.get_sentiment_raw("Hello World")
				LOG.info("Successfully tested connection")
				return
			except Exception as e:
				LOG.info("socket connection could not be made (%s)" % e)
				if i < num_retries-1:
					LOG.info("pausing before retry")
					time.sleep(5)
		assert False, "The socket could not be obtained"

	def get_sentiment_raw(self, text):
		self.send_text(text)
		output = self.receive_text()
		return output

	def receive_text(self):
		size_info_str = self.sock.recv(8)
		size_info = struct.unpack('>Q', size_info_str)[0]

		chunks = []
		curlen = lambda: sum(len(x) for x in chunks)
		while True:
			data = self.sock.recv(size_info - curlen())
			chunks.append(data.decode(self.encoding, 'ignore'))
			if curlen() >= size_info: break
			if len(chunks) > 1000:
				LOG.warning("Incomplete value from socket")
				return None
			#time.sleep(0.01)
		return ''.join(chunks)

	def send_text(self, text):
		try:
			data = bytes( text + "\n", self.encoding, 'ignore')
		except Exception as e:
			try:
				data = (text + "\n").encode(self.encoding, 'ignore')
			except Exception as ex:
				data = (text + "\n").decode(self.encoding, 'ignore').encode(self.encoding, 'ignore')
		sz = len(data)
		len_info = struct.pack('>Q', sz)
		self.sock.sendall(len_info)
		self.sock.sendall( data )

	def process_raw_output(self, output, merge_results=False):
		output = output.replace('\r', '')
		lines1 = output.split('\n')
		lines = []
		i = -1
		for l in lines1:
			if not l.strip() == '':
				if i < 0 and l.find('(0') >= 0:
					i = len(lines)
				lines.append(l)
		return_value = []
		global g_lines
		g_lines = lines
		if i == -1:
			i = 0
		while True:
			#print(i)
			if i+1 >= len(lines):
				break
			tree_string = lines[i].strip()
			#print(tree_string)
			#LOG.info(i)
			#LOG.info("The tree string is %s" % tree_string)
			g_tree_string = tree_string
			try:
				tree = ParentedTree.fromstring(tree_string.strip())
			except Exception as ex:
				tree = ''
				LOG.info("got exception processing tree(%s) %s" % (tree_string, ex))
				break
			probs = re.sub(' +', ' ', lines[i+1].strip()).split(' ')[1:]
			score = self.probs_to_score(probs)
			nodes = len(list(tree.subtrees()))
			#LOG.info("the number of nodes are %d" % nodes)
			i = i + nodes+1
			#print("Nodes: %d" % nodes)
			#print(i)
			sentence = ' '.join(tree.leaves())
			sentence = re.sub(" +", " ", sentence)
			sentence = re.sub(" \.", ".", sentence)
			return_value.append({"score":score, "tree":tree, "text":sentence})
		if merge_results:
			return_value_1 = {}
			texts = []
			s = 0
			for rv in return_value:
				s = s + rv["score"]
				texts.append(rv['text'])
			n = len(return_value)
			if n == 0:
				n = 1
			return_value_1['score'] = s/n
			return_value_1['text'] = ' '.join(texts)
			return return_value_1
		return return_value

	def probs_to_score(self, probs):
		l2 = math.floor(len(probs)/2)
		classes = range( int(-l2), int(l2)+1 )
		x = 0
		for i in range(len(probs)):
			p = probs[i]
			if type(p).__name__ == 'str':
				p = float(p)
			x = x + classes[i]*p
		return (x + l2)/(2.0*l2)

	def get_sentiment_and_process( self, text, merge_results=False ):
		return self.process_raw_output(self.get_sentiment_raw( text ), merge_results=merge_results)

	def get_sentiment_of_sentences_and_process(self, sentences, merge_results=True):
		results = []
		for sentence in sentences:
			if merge_results:
				results.append( self.get_sentiment_and_process( sentence, True ) )
			else:
				results.extend( self.get_sentiment_and_process( sentence, False ) )
		return results


	def close(self):
		self.sock.close()


if __name__ == '__main__':
	port = int(sys.argv[1])
	sspl_client = SSPLClient(port)
	sspl_client.connect_to_server()
	LOG.info("Enter 'quit' to quit")
	# while True:
	# 	input = sys.stdin.readline()
	# 	if input.strip() == 'quit':
	# 		break
	# 	output = sspl_client.get_sentiment_raw(input)
	# 	LOG.info( output )
	# 	LOG.info("")
	# sspl_client.close()
	