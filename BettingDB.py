
import MySQLdb, datetime
from config import CONFIG as config
import uuid, time

class BettingDB():

    def __init__(self):     
        self.db = MySQLdb.connect(passwd=config["mysql"]["pw"],host="localhost",
            user="root", db="betting")
        self.cursor = self.db.cursor()
        self.date = datetime.datetime.now()

    def execute_command(self, query_string):
        print "{}\n\n".format(query_string)
        self.cursor.execute(query_string)

        self.db.commit()


    def add_moneyline(self, line, game_id):
        # print type(game["home_line"])
        # print type(game["away_line"])

        if not self.lines_table_exists(line["sport"]):
            # if table does not exist
            print "{}_lines does not exist".format(line[sport])
            self.create_moneyline_table(line["sport"])

        print "Ensuring proper format"

        # Make sure all odds are in decimal form (not American)
        if abs(line["home_line"]) > 99:
            line["home_line"] = convert_odds(line["home_line"],"american","decimal")
        if abs(line["away_line"]) > 99:
            line["away_line"] = convert_odds(line["away_line"],"american","decimal")

        print "Adding moneyline"

        line["id"] = self.get_game_id(line)

        query_string = """INSERT INTO {7}_lines (poll_time, id, site, home_team, home_line, away_team, away_line)
    VALUES ({0},{1},\'{2}\',\'{3}\',{4},\'{5}\',{6})""".format(line["poll_time"], line["id"], line["site"],line["home_team"],
    line["home_line"], line["away_team"], line["away_line"], line["sport"])
        self.execute_command(query_string)

    def create_moneyline_table(self,sport):
        query_string = """CREATE TABLE {}_lines (poll_time TEXT, id INT, site TEXT, 
home_team TEXT, home_line DOUBLE(4,3), away_team TEXT, away_line DOUBLE(4,3))""".format(sport)
        # print query_string
        self.execute_command(query_string)

    def lines_table_exists(self, sport):
        stmt = "SHOW TABLES LIKE \'{}_lines\'".format(sport)
        self.cursor.execute(stmt)
        result = self.cursor.fetchone()
        if result:
            return True
        else:
            return False

    def ids_table_exists(self):
        stmt = "SHOW TABLES LIKE \'game_ids\'"
        self.cursor.execute(stmt)
        result = self.cursor.fetchone()
        if result:
            return True
        else:
            return False

    def create_ids_table(self):
        query_string = """CREATE TABLE game_ids (id INT, day TEXT, time TEXT, home_team TEXT, away_team TEXT, sport TEXT)"""
        # print query_string
        self.execute_command(query_string)


    def get_moneylines(self, game):

        game_id = self.get_game_id(game)
        query_string = """SELECT home_line, away_line, poll_time FROM {0}_lines 
            WHERE id = {1} """.format(game["sport"],game_id)

        self.cursor.execute(query_string)

        money_line_lists = self.cursor.fetchmany(100)

        money_line_dictionaries = self.convert_lines_to_dictionaries(money_line_lists)

        return money_line_dictionaries

    def convert_lines_to_dictionaries(self,games):

        money_line_dictionaries = []

        for game in games:
            money_line_dictionaries.append({"home_line":game[0],"away_line":game[1],
                "poll_time":game[2]})

        return money_line_dictionaries

    def check_game_exists(self,game):

        if not self.ids_table_exists():
            print "game_ids table does not exist"
            self.create_ids_table()

        query_string = """SELECT id FROM game_ids 
            WHERE home_team = \'{0}\' 
            AND away_team = \'{1}\'
            AND day = \'{2}\'
            AND time = \'{3}\'
            AND sport = \'{4}\'""".format(game["home_team"],
            game["away_team"],game["game_time"]["day"],game["game_time"]["time"] , game["sport"])

        # print "{}".format(query_string)
        self.cursor.execute(query_string)
        try:
            # attempts to get the result 

            result = self.cursor.fetchone()[0]

            print result

        except:
            #if it fails, make a new id
            result = None

        return result

    def get_game_id(self, game):
        # we can assume that all the games in the id database are in the next 2 days

        if not self.ids_table_exists():
            print "game_ids table does not exist"
            self.create_ids_table()

        query_string = """SELECT id FROM game_ids 
            WHERE home_team = \'{0}\' 
            AND away_team = \'{1}\'
            AND day = \'{2}\'
            AND time = \'{3}\'
            AND sport = \'{4}\'""".format(game["home_team"],
            game["away_team"],game["game_time"]["day"],game["game_time"]["time"] , game["sport"])
            
        self.cursor.execute(query_string)
        try:
            # attempts to get the result 
            result = self.cursor.fetchone()[0]
        except:
            #if it fails, make a new id
            result = self.add_id(game)

        return result

    def add_id(self,game):
        
        if not self.ids_table_exists():
            print "game_ids table does not exist"
            self.create_ids_table()


        if not self.lines_table_exists(game["sport"]):
            print "{}_lines table does not exist".format(game["sport"])
            self.create_moneyline_table(game["sport"])

        print "Making new id"

        self.cursor.execute("""SELECT MAX(id) AS id FROM {}_lines""".format(game["sport"]))
        largest_id = self.cursor.fetchone()[0]

        # print self.cursor.fetchone()

        if largest_id:
            new_id = largest_id + 1
        else:
            new_id = 1
        
        query_string = """INSERT INTO game_ids (id,home_team,away_team,sport,day)
VALUES ({0},\'{1}\',\'{2}\',\'{3}\',\'{4}\')""".format(new_id,game["home_team"],game["away_team"],
            game["sport"],game["game_time"]["day"])

        self.cursor.execute(query_string)

        # print query_string
        
        self.db.commit()

        return new_id

    def delete_id(self,game):
        #only delete if game exists
        game_id = self.check_game_exists(game)


        if game_id:    
            print "Deleting id"
            query_string = """DELETE FROM game_ids WHERE id = {0} AND sport = '{1}' """.format(
                game_id,game["sport"])      
            # print query_string
            self.cursor.execute(query_string)

    def shutdown(self):
        self.db.disconnect()

# Converts odds from currentType to desiredType (can be "american" or "decimal")
def convert_odds(odds, currentType, desiredType):

    if currentType == "american":
        if odds > 0:
            convertedOdds = 1+odds/100.
        else:
            convertedOdds = 1-100./odds
    elif currentType == "decimal":
        if odds >= 2:
            convertedOdds = (odds-1)*100.
        else:
            convertedOdds = 100./(1-odds)

    return convertedOdds


