# Importation des modules
from os.path import exists, join
from time import strftime, ctime
from tkinter import Frame, Text
from threading import Thread
from os import mkdir

# Variables globales du module
DEFAULT_DIR = "Logs"
LEVELS = ["Debug", "Info", "Warning", "Error"]
LEVELS_COLORS = ["grey", "white", "orange", "red"]

# Création des objets du module
class Logger(Frame):
	"""
	Logger API
	To change save directory use Logger(directory="your_dir")
	"""
	def __init__(self, parent, directory=DEFAULT_DIR):
		# Initialisation des dépendances
		Frame.__init__(self, parent)

		# Construction des widgets
		self.widget = Text(self, fg="white", bg="black", state="disabled")
		for i, level in enumerate(LEVELS):
			self.widget.tag_config(level, foreground=LEVELS_COLORS[i], background="black")
		self.widget.pack(fill="both", expand="yes")

		# Création des attributs du logger
		self.logs = []
		self.dir = directory
		self.log_filter = 0

	def log(self, level, msg, thread="MAIN-THREAD", thread_id=-1):
		if thread_id == -1:
			log = "[{}][{}][{}]: {}".format(ctime(), thread, LEVELS[level], msg)
		else:
			log = "[{}][{}-{}][{}]: {}".format(strftime("%H-%M-%s"), thread, thread_id, LEVELS[level], msg)
		print(log)
		self.logs.append((level, log))

		# Update du Widget
		self.widget.config(state="normal")
		self.widget.insert("end", log+"\n", LEVELS[level])
		self.widget.config(state="disabled")

	def save(self, filter=0):
		if not exists(self.dir):
			mkdir(self.dir)
		filename = join(self.dir, "log_of_{}.log".format(strftime("%Y_%m_%d")))
		with open(filename, "wb") as file:
			for log in self.logs:
				if log[0] >= filter:
					file.write("{}\n".format(log[1]).encode())
			file.close()

	def get_logs(self, filter=0):
		return [log for log in self.logs if log[0] >= filter]

	def set_filter(self, filter):
		self.log_filter = filter
