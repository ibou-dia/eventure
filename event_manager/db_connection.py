import pymongo


# url ="mongodb+srv://charbeladonis54:Fz5swlWwnxsLidjm@clusterdjango.sseokfp.mongodb.net/"
url ="mongodb://localhost:27017"
client = pymongo.MongoClient(url)

db=client['mongodbDjango']