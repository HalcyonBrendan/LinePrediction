import MySQLdb, datetime
from config import CONFIG as config
import uuid, time

class BettingDB():

    def __init__(self):     
        self.db = MySQLdb.connect(passwd=config["mysql"]["pw"],host="localhost",user="root", db="betting")
        self.cursor = self.db.cursor()
        self.date = datetime.datetime.now()

    def execute_command(self, query_string):
        print "{}\n".format(query_string)
        self.cursor.execute(query_string)
        self.db.commit()

    def execute_query(self, query_string):
        self.cursor.execute(query_string)
        sqlOut = self.cursor.fetchall()
        return sqlOut

    def add_moneyline(self, line, game_id):
        # print type(game["home_line"])
        # print type(game["away_line"])

        if not self.lines_table_exists(line["league"]):
            # if table does not exist
            print "{}_lines does not exist".format(line[league])
            self.create_moneyline_table(line["league"])

        line["id"] = self.get_game_id(line)

        # Make sure all odds are in decimal form (not American)
        if abs(line["home_line"]) > 99:
            line["home_line"] = convert_odds(line["home_line"],"american","decimal")
        if abs(line["away_line"]) > 99:
            line["away_line"] = convert_odds(line["away_line"],"american","decimal")

        # Check to see if line has changed since last check
        query_string = """SELECT home_line FROM {0}_lines WHERE id={1} AND site=\'{2}\' ORDER BY poll_time DESC LIMIT 1;""".format(line["league"],line["id"],line["site"])
        previous_home_line = self.strip_unwanted_text(str(self.execute_query(query_string)))
        if len(previous_home_line) > 0:
            previous_home_line = float(previous_home_line)
        else:
            previous_home_line = -1
        query_string = """SELECT away_line FROM {0}_lines WHERE id={1} AND site=\'{2}\' ORDER BY poll_time DESC LIMIT 1;""".format(line["league"],line["id"],line["site"])
        previous_away_line = self.strip_unwanted_text(str(self.execute_query(query_string)))
        if len(previous_away_line) > 0:
            previous_away_line = float(previous_away_line)
        else:
            previous_away_line = -1

        if abs(line["home_line"]-previous_home_line) < 0.001 and abs(line["away_line"]-previous_away_line) < 0.001:
            print "Line in game of ", line["away_team"], " at ", line["home_team"], " has not changed. Continuing to next line..."
            return

        print "Adding moneyline"

        query_string = """INSERT INTO {8}_lines (poll_time, id, game_time, home_team, home_line, away_team, away_line, site)
    VALUES ({0},{1},{2},\'{3}\',{4},\'{5}\',{6},\'{7}\')""".format(line["poll_time"], line["id"], line["game_time"], line["home_team"],
    line["home_line"], line["away_team"], line["away_line"],line["site"],line["league"])
        self.execute_command(query_string)


    def create_moneyline_table(self,league):
        query_string = """CREATE TABLE {}_lines (poll_time INT, id INT, game_time INT,
    home_team TEXT, home_line DOUBLE(8,4), away_team TEXT, away_line DOUBLE(8,4), site TEXT)""".format(league)
        # print query_string
        self.execute_command(query_string)

    def lines_table_exists(self, league):
        stmt = "SHOW TABLES LIKE \'{}_lines\'".format(league)
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
        query_string = """CREATE TABLE game_ids (id INT, game_time TEXT, home_team TEXT, away_team TEXT, league TEXT)"""
        # print query_string
        self.execute_command(query_string)


    def get_moneylines(self, game):

        game_id = self.get_game_id(game)
        query_string = """SELECT home_line, away_line, poll_time FROM {0}_lines 
            WHERE id = {1} """.format(game["league"],game_id)

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
            AND game_time = \'{2}\'
            AND league = \'{3}\'""".format(game["home_team"],
            game["away_team"],game["game_time"], game["league"])

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
            AND game_time < {2}+12000
            AND game_time > {2}-12000
            AND league = \'{3}\';""".format(game["home_team"],
            game["away_team"],game["game_time"], game["league"])

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

        if not self.lines_table_exists(game["league"]):
            print "{}_lines table does not exist".format(game["league"])
            self.create_moneyline_table(game["league"])

        print "Making new id for ", game["away_team"], " at ", game["home_team"]

        query = "SELECT MAX(id) FROM game_ids WHERE league=\'{0}\';".format(game["league"])
        max_id = self.execute_query(query)[0][0]

        if max_id:
            new_id = max_id + 1
        else:
            new_id = 1

        query = """INSERT INTO game_ids (id,home_team,away_team,league,game_time) VALUES ({0},\'{1}\',\'{2}\',\'{3}\',\'{4}\')""".format(new_id,game["home_team"],game["away_team"],game["league"],game["game_time"])
        self.execute_command(query)

        return new_id

    def delete_id(self,game):
        #only delete if game exists
        game_id = self.check_game_exists(game)


        if game_id:    
            print "Deleting id"
            query_string = """DELETE FROM game_ids WHERE id = {0} AND league = \'{1}\' """.format(game_id,game["league"])      
            # print query_string
            self.cursor.execute(query_string)

    def strip_unwanted_text(self,my_str):
        
        chars_to_strip = ["(", ")", ",", " "]
        for item in chars_to_strip:
            # print "\'{0}\' in \'{1}\'? {2}".format(item, my_str, item in my_str)
            my_str = my_str.replace(item,'')

        return my_str

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


