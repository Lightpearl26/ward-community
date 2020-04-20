# Importation des modules
from socket import AF_INET, SOCK_STREAM, socket
from os.path import join, exists
from threading import Thread
from select import select
from tkinter import Frame
from queue import Queue
from os import mkdir

# Importation des modules du package
from . import logger

# Création des variables globales du module
SERVER_PORT = 443
BAN_FOLDER = join("Data", "Bans")
INFOS_FOLDER = join("Data", "Infos")
LOG_FOLDER = join("Data", "Logs")

# Création des objets du module
class Room:
	"""
	One Room of the main server
	"""
	def __init__(self, server):
		self.message_queue = Queue()
		self.server = server
		self.clients = {}

	def send(self, msg, client_names=None):
		if client_names:
			for name in client_names:
				self.clients[name]["conn"].send(msg.encode())
		else:
			for name in self.clients:
				self.clients[name]["conn"].send(msg.encode())

	def add_client(self, name, conn, conn_infos):
		self.clients[name] = {"conn": conn, "infos": conn_infos}

class Server(Frame):
	"""
	TPC server getting messages and sending it to differents rooms
	"""
	def __init__(self, parent):
		# Initialisation de l'héritage
		Frame.__init__(self, parent)

		# Création des objets du serveur
		self.conn = socket(AF_INET, SOCK_STREAM)
		self.logger = logger.Logger(parent, directory=LOG_FOLDER)

		# Création des salles du serveur
		self.room_names = []
		self.rooms = {}
		self.bans = {}

		# Création des files d'attente du serveur
		self.send_queue = Queue()
		self.recv_queue = Queue()
		self.accept_conn_queue = Queue()

		# Initialisation des attributs d'étât du serveur
		self.running = True

	def add_room(self, room_name):
		self.rooms[room_name] = Room(self)
		self.room_names.append(room_name)
		self.load_banlist(room_name)

	def close_room(self, room):
		for client_name, client in self.rooms[room].clients:
			self.kick(room, client_name, message="Closing the room")
		self.save_banlist(room)

	def accept_conn(self):
		pass

	def kick(self, room, client_name, message=None):
		pass

	def ban(self, room, client_name, message=None):
		self.kick(room, client_name, message)
		if not client_name in self.bans[room]:
			self.bans[room].append(client_name)

	def pardon(self, room, client_name):
		if client_name in self.bans[room]:
			self.bans[room].remove(client_name)

	def send(self, msg, room):
		#self.rooms[room].
		pass

	def load_banlist(self, room):
		if not exists(BAN_FOLDER):
			mkdir(BAN_FOLDER)
		self.bans[room] = []
		if exists(join(BAN_FOLDER, "{}.data".format(room))):
			with open(join(BAN_FOLDER, "{}.data".format(room)), "rb") as file:
				for line in file:
					self.bans[room].append(line[:-1])
				file.close()

	def save_banlist(self, room):
		if not exists(BAN_FOLDER):
			mkdir(BAN_FOLDER)
		with open(join(BAN_FOLDER, "{}.data".format(room)), "wb") as file:
			for ban in self.bans[room]:
				file.write("{}\n".format(ban))
			file.close()

	def serve_forever(self):
		while self.running:
			pass

class Client:
	"""
	"""
	def __init__(self, name, room):
		self.conn = socket(AF_INET, SOCK_STREAM)
		self.name = name
		self.room = room
