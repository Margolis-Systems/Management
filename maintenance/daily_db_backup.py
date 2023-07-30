import sys
sys.path.insert(1, 'C:\\Server')
from configs import mongo

if __name__ == '__main__':
    mongo.dump("C:\\DB_backup")
