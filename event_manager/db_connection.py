import pymongo

url = (
    "mongodb+srv://charbeladonis54:Fz5swlWwnxsLidjm@clusterdjango.sseokfp.mongodb.net/"
)
client = pymongo.MongoClient(url)
db = client["mongodbDjango"]
