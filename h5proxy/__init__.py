from h5proxy import Group, Dataset, File, HardLink, SoftLink, ExternalLink

def startServer():
    from h5proxy import Server
    server = Server()
    server.start()

