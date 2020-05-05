# -*- coding: utf-8 -*-

# Importation des modules du package
from . import logger

# Importation des modules externes
from os import mkdir, listdir
from queue import Queue, Empty
from select import select, error
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from tkinter import Frame, Menu, Listbox, Label, Entry, END

# Variables globales du module
BAN_FOLDER = "Server-Bans"
CLIENT_HOST = ("ward-community.ddns.net", 12345)
CLIENT_LOG_FOLDER = "Client-Logs"
INFOS_FOLDER = "Server-Infos"
SERVER_HOST = ("192.168.1.16", 12345)
SERVER_LOG_FOLDER = "Server-Logs"

# Objets du module
class Client(Frame):
	"""
	TCP Client connected to the Server
	"""
	def __init__(self, parent, name, room):
		# Initialisation des dépendances
		Frame.__init__(self, parent)

		# Création des attributs
		self.name = name
		self.room = room

		# Création des booléens
		self.is_listenning = False

		# Affection des objets tierces
		self.logger = logger.Logger(self, directory=CLIENT_LOG_FOLDER)
		self.conn = socket(AF_INET, SOCK_STREAM)

		# Création des files d'exécution
		self.messages = Queue()
		self.commands = Queue()

		# Création des Threads
		self.listen_thread = Thread(target=self.listen_to_server)
		self.exec_thread = Thread(target=self.process_message)

		# Lancement des méthodes de construction
		self.build_frame()

		# Logs
		self.logger.log(0, "The CLient has been built")

	def build_frame(self):
		"""
		Method used to build the tkinter Frame of the Client 
		"""
		pass

	def close(self):
		"""
		Method used to close the connection between the client and the server
		"""
		self.conn.send("CLOSE;{};{}".format(self.room, self.name).encode())
		self.is_listenning = False
		self.listen_thread.join()
		self.exec_thread.join()
		self.conn.close()
		self.logger.log(1, "Succesfully closed the connection with server", thread="CLIENT-THREAD")

	def connect(self):
		"""
		Method used to connect the client to the server
		"""
		self.conn.connect(CLIENT_HOST)
		self.conn.send("ASKCO;{};{}".format(self.room, self.name).encode())
		self.is_listenning = True
		self.listen_thread.start()
		self.exec_thread.start()
		self.logger.log(1, "Succesfully connected the server", thread="CLIENT-THREAD")

	def listen_to_server(self):
		"""
		Method linked to the thread used to listen to the server
		"""
		while self.is_listenning:
			try:
				to_read, _, _ = select([self.conn], [], [], 0.05)
			except error:
				pass
			except ValueError:
				pass
			else:
				try:
					for server in to_read:
						msg = server.recv(9999999).decode()
						self.messages.put(msg)
						self.logger.log(0, "Recieved message [{}] from server".format(msg), thread="CLIENT-LSITENNER-THREAD")
				except OSError:
					pass
	
	def process_message(self):
			"""
			Method linked to the Thread used to execute command on messages got from the server
			"""
			while self.is_listenning:
				if not self.messages.empty():
					try:
						msg = self.messages.get(timeout=0.05)
					except Empty:
						pass
					else:
						cmd = msg.split(";")
						if cmd[0] == "KICKED":
							self.close()
							self.logger.log(2, "The server kicked you for the following reason: {}".format(";".join(cmd[:1])), thread="CLIENT-THREAD")
						elif cmd[0] == "BANED":
							self.close()
							self.logger.log(2, "The server baned you for the following reason: {}".format(";".join(cmd[:1])), thread="CLIENT-THREAD")
						else:
							self.commands.put(msg)

	def send(self, message):
		"""
		Method used to send a message to the server
		"""
		self.conn.send("MESSA;{};{};{}".format(self.room, self.name, message).encode())

class Server(Frame):
	"""
	TCP central Server
	"""
	def __init__(self, parent):
		# Initialisation des dépendances
		Frame.__init__(self, parent)

		# Création des attributs
		self.bans = {}
		self.clients = []
		self.rooms = {}
		self.room_names = []

		# Création des booléens
		self.is_serving = False

		# Affectation des objets tierces
		self.conn = socket(AF_INET, SOCK_STREAM)
		self.logger = logger.Logger(self, directory=SERVER_LOG_FOLDER)

		# Création des files d'exécution
		self.conn_queue = Queue()
		self.recv_queue = Queue()
		self.send_queue = Queue()

		# Création des Threads
		self.threads = [

		]

		# Lancement des méthodes de construction
		self.init_rooms()
		self.load_banlists()
		self.build_frame()

		# Logs
		self.logger.log(0, "The server has been built")

	def add_room(self, name):
		"""
		Method used to add a new room to the server
		"""
		pass

	def ban(self, room, name):
		"""
		Method used to ban a client from the server
		"""
		pass

	def build_frame(self):
		"""
		Method used to build the tkinter Frame of the server 
		"""
		pass

	def init_rooms(self):
		"""
		Method used to initialise the rooms of the server
		"""
		pass

	def load_banlists(self):
		"""
		Method used to load the banlist saved on a file
		"""
		pass

	def save_banlists(self):
		"""
		Method used to save the banlist in a file
		"""
		pass
