# Importation des modules
from tkinter import Tk, Frame, Menu, Listbox, Label, Entry, END
from socket import AF_INET, SOCK_STREAM, socket
from urllib.request import Request, urlopen
from select import select, error
from os.path import join, exists
from queue import Queue, Empty
from os import mkdir, listdir
from threading import Thread
from time import sleep

# Importation des modules du package
from . import logger

# Création des variables globales du module
print("Loading constants")
SERVER_IP = "192.168.1.16" # urlopen(Request("https://api.ipify.org/?format=txt", headers={"User-Agent": "Mozilla/5.0"})).read().decode()
SERVER_PORT = 12345
SERVER_HOST = (SERVER_IP, SERVER_PORT)
BAN_FOLDER = "Server-Bans"
INFOS_FOLDER = "Server-Infos"
LOG_FOLDER = "Server-Logs"

# Création des objets du module
print("loading objects")
class Room:
	"""
	One Room of the main server
	"""
	def __init__(self, server):
		self.message_queue = Queue()
		self.server = server
		self.clients = {}

	def send(self, msg, client_names=[]):
		if not client_names == []:
			for name in client_names:
				self.clients[name]["conn"].send(msg.encode())
		else:
			for name in self.clients:
				self.clients[name]["conn"].send(msg.encode())

	def add_client(self, name, conn, conn_infos):
		self.clients[name] = {"conn": conn, "infos": conn_infos}
	
	def remove_client(self, name):
		self.clients[name]["conn"].close()
		del self.clients[name]

class Server(Tk):
	"""
	TPC server getting messages and sending it to differents rooms
	"""
	def __init__(self):
		# Initialisation de l'héritage
		Tk.__init__(self)

		# Création des objets du serveur
		self.conn = socket(AF_INET, SOCK_STREAM)
		self.logger = logger.Logger(self, directory=LOG_FOLDER)
		self.logger.log(0, "Initialising the server")

		# Création des salles du serveur
		self.room_names = []
		self.rooms = {}
		self.bans = {}
		self.clients = []

		# Création des files d'attente du serveur
		self.send_queue = Queue()
		self.recv_queue = Queue()
		self.accept_conn_queue = Queue()

		# Initialisation des attributs d'étât du serveur
		self.running = True
		self.selected_room = None

		# Initialisation des travailleurs chinois jaunes du serveur
		self.workers = [
			Thread(target=self.serve_forever),
			Thread(target=self.accept_conn),
			Thread(target=self.process_sending)
		]

		# Initialisation de la liste des salles de la GUI
		self.room_list = Listbox(self)

		# Initialisation de la liste des clients de la GUI
		self.client_list = Listbox(self)
		self.ban_list = Listbox(self)

		# Initialisation de la zone de commande de la GUI
		self.input_frame = Frame(self)
		self.input_label = Label(self.input_frame, text=">>")
		self.input_command = Entry(self.input_frame, width=150)

		# Affchage des différents éléments
		self.client_list.grid(row=0, column=0, rowspan=3, sticky="nsew")
		self.ban_list.grid(row=0, column=1, rowspan=3, sticky="nsew")
		self.input_label.grid(row=0, column=0, sticky="nsew")
		self.input_command.grid(row=0, column=1, sticky="nsew")
		self.input_frame.grid(row=3, column=0, columnspan=3, sticky="nsew")
		self.logger.grid(row=0, column=2, sticky="nsew")
		self.room_list.grid(row=1, rowspan=2, column=2, sticky="nsew")

		# Initialisation des salles
		for room in listdir(BAN_FOLDER):
			self.add_room(room[:-5])

	def add_room(self, room_name):
		self.rooms[room_name] = Room(self)
		self.room_names.append(room_name)
		self.load_banlist(room_name)
		self.logger.log(0, "Adding room {} to server".format(room_name))

	def close_room(self, room):
		for client_name in self.rooms[room].clients:
			self.kick(room, client_name, message="Closing the room")
		self.save_banlist(room)
		self.logger.log(0, "Closing room {}".format(room))

	def accept_conn(self):
		while self.running:
			if not self.accept_conn_queue.empty():
				try:
					conn, conn_infos = self.accept_conn_queue.get(timeout=0.05)
				except Empty:
					conn, conn_infos = None, None
				if conn and conn_infos:
					msg = conn.recv(9999).decode()
					if ";" in msg:
						if msg[:5] == "ASKCO":
							room, name = msg.split(";")[1:]
							if room in self.room_names:
								if not name in self.bans[room]:
									self.rooms[room].add_client(name, conn, conn_infos)
									self.clients.append(conn)
									self.logger.log(1, "Say Hello to {} joining the server with {}".format(name, conn_infos))
								else:
									conn.send("BANED;Your are baned from this server".encode())
									conn.close()
									self.logger.log(2, "Client {} tryied to come but probably forget that he was baned".format(name))
							else:
								self.add_room(room)
								self.rooms[room].add_client(name, conn, conn_infos)
								self.clients.append(conn)
								self.logger.log(1, "Say Hello to {} joining the server with {}".format(name, conn_infos))
						else:
							conn.send("KICKD;Bad indetifying".encode())
							conn.close()
							self.logger.log(2, "Something tryed to access server without identifying itself")
					else:
						conn.send("KICKD;Bad indetifying".encode())
						conn.close()
						self.logger.log(2, "Something tryed to access server without identifying itself")
		self.logger.log(1, "Server stop accept connection")

	def connected(self, client_name):
		for room in self.room_names:
			if client_name in self.rooms[room].clients:
				return True, room
		return False, None

	def kick(self, room, client_name, message=""):
		if self.connected(client_name)[0]:
			self.rooms[room].send("KICKD;{}".format(message), client_names=[client_name])
		self.rooms[room].remove_client(client_name)
		self.logger.log(1, "Kicking {} from room {}".format(client_name, room))

	def ban(self, room, client_name, message=""):
		self.kick(room, client_name, message)
		if not client_name in self.bans[room]:
			self.bans[room].append(client_name)
		self.logger.log(2, "Banning {} from room {}".format(client_name, room))

	def pardon(self, room, client_name):
		if client_name in self.bans[room]:
			self.bans[room].remove(client_name)
		self.logger.log(2, "Server know how to say pardon to {} of room {}".format(client_name, room))

	def send(self, msg, room, client_names=[]):
		self.send_queue.put((msg, room, client_names))

	def load_banlist(self, room):
		if not exists(BAN_FOLDER):
			mkdir(BAN_FOLDER)
		self.bans[room] = []
		if exists(join(BAN_FOLDER, "{}.data".format(room))):
			with open(join(BAN_FOLDER, "{}.data".format(room)), "r") as file:
				for line in file:
					self.bans[room].append(line[:-1])
				file.close()
		self.logger.log(0, "Loading banlist of the room {}".format(room))

	def save_banlist(self, room):
		if not exists(BAN_FOLDER):
			mkdir(BAN_FOLDER)
		with open(join(BAN_FOLDER, "{}.data".format(room)), "w") as file:
			for ban in self.bans[room]:
				file.write("{}\n".format(ban))
			file.close()
		self.logger.log(0, "Save banlist of the room {}".format(room))

	def process_sending(self):
		while self.running:
			if not self.send_queue.empty():
				try:
					msg, room, client_names = self.send_queue.get(timeout=0.05)
				except Empty:
					msg, room, client_names = None, None, None
				if msg and room:
					msg, room, client_names = self.send_queue.get()
					self.rooms[room].send(msg, client_names)
					self.logger.log(1, "Sending {} to room {} to clients {}".format(msg, room, client_names))
		self.logger.log(1, "Server stop sending messages")

	def serve_forever(self):
		self.conn.bind(SERVER_HOST)
		self.logger.log(1, "Server is running on {}".format(SERVER_HOST))
		self.conn.listen(5)
		while self.running:
			try:
				askcos, _, _ = select([self.conn], [], [], 0.05)
				for askco in askcos:
					conn, conn_infos = askco.accept()
					self.accept_conn_queue.put((conn, conn_infos))
			except error:
				pass

			to_read = []
			try:
				to_read, _, _ = select(self.clients, [], [], 0.05)
			except error:
				pass
			except ValueError:
				pass
			else:
				try:
					for conn in to_read:
						msg = conn.recv(9999).decode()
						self.recv_queue.put(msg)
				except OSError:
					pass
		self.logger.log(1, "Server is now offline")
		
	def start(self):
		self.logger.log(2, "Starting the server")
		for worker in self.workers:
			worker.start()

	def shutdown(self):
		self.running = False
		self.logger.log(2, "The server has been shutdowned")

	def stop(self):
		self.logger.log(2, "stopping the server")
		for worker in self.workers:
			worker.join()
		print("Chinois morts")
		for conn in self.clients:
			conn.close()
		print("Tout est fermé")
		self.logger.save()

		del self

	def exec_command(self, event=None):
		command = self.input_command.get()
		self.input_command.delete(0, END)
		self.logger.log(1, "Recieving command {} from GUI".format(command))
		infos = command.split(" ")
		if infos[0] == "kick":
			self.kick(infos[1], infos[2], message="you have been kicked by the server GUI")
		if infos[0] == "ban":
			self.ban(infos[1], infos[2], message="you have been kicked by the server GUI")

	def set_room_selection(self, event=None):
		room = self.room_list.curselection()
		if room and room != self.selected_room:
			self.selected_room = room[0]
		print(self.selected_room)

	def update_display(self):
		self.room_list.delete(0, END)
		self.client_list.delete(0, END)
		self.ban_list.delete(0, END)
		for i, name in enumerate(self.room_names):
			self.room_list.insert(i, name)
		if self.selected_room:
			self.room_list.selection_set(self.selected_room)
		self.room_list.update()
		if self.selected_room:
			for i, name in enumerate([name for name in self.rooms[self.room_names[self.selected_room]].clients.keys()]):
				self.client_list.insert(i, name)
			self.client_list.update()
			for i, name in enumerate(self.bans[self.room_names[self.selected_room]]):
				self.ban_list.insert(i, name)
			self.ban_list.update()
		self.logger.update_display()
		self.input_command.update()

	def mainloop(self):
		for room in self.rooms:
			self.load_banlist(room)
		self.start()

		self.title("Ward-Community | Server")
		self.resizable(False, False)
		self.protocol("WM_DELETE_WINDOW", self.shutdown)
		self.input_command.bind("<Return>", self.exec_command)
		self.room_list.bind("<Button-1>", self.set_room_selection)

		while self.running:
			self.update_idletasks()
			self.update_display()

		for room in self.rooms:
			self.save_banlist(room)
		self.stop()
		exit()

class Client:
	"""
	"""
	def __init__(self, name, room):
		self.conn = socket(AF_INET, SOCK_STREAM)
		self.name = name
		self.room = room
