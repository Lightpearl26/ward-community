from libs.pyTPC import Client

name = input("Your name : ")
room = input("Your room : ")

client = Client(name, room)
client.connect()
while client.listening:
	cmd = input(">>> ")
	if cmd == "close":
		client.close()
	else:
		client.send(cmd)