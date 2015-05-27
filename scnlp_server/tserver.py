import sys
from threading import Thread

class tserver():
	def __init__(self):
		self.stop_server = False
		self.server_socket = None
		self.proc = None

	def shutdown( self ):
		print("Shutting down the server")
		self.stop_server = True
		self.server_socket.close()
		self.server_thread.join()
		self.proc = None
		print("Server shut down successfully")

	def wait_for_command(self):
		while True:
			print("Enter 'quit' to shut down the server")
			input = sys.stdin.readline()
			if input.strip() == 'quit':
				self.shutdown()
				break
				return
			else:
				print("Unknown Command")

	def accept_clientes(self):
		try:
			print(self.stop_server)
			while not self.stop_server:
				(clientsocket, address) = self.server_socket.accept()
				thread = Thread(target = self.handle_client, args = ( clientsocket, ))
				thread.daemon = True
				thread.start()
		except Exception as ex:
			self.server_socket.close()
			#LOG.info("An exception occured %s" % ex)
		print("Server is shutting down...")