# from bs4 import BeautifulSoup
import re, time, sys, datetime, math, signal
import HTML_parser
import Emailer
import BettingDB
import random
import json

def print_json(json_object):
    print json.dumps(json_object, indent=4, sort_keys=True)
    print "\n"

class OddsComparer():

    def __init__(self):
        self.parser = HTML_parser.HTML_parser()
        self.bets_DB = BettingDB.BettingDB()
        self.emailer = Emailer.Emailer()
        self.games = {}
        self.date = datetime.datetime.now()

        random.seed(int(time.time()))

    def run(self):
        # get the money lines for each website
        while True:

            self.games = self.parser.get_moneylines()
            results = []

            # print_json(self.games)

            # for sport in self.games:
            for group in self.games:
                # check to see if game id exsists in
                site = group["site"]
                # print site
                for game in group["moneylines"]:

                    """
                    your code for what to do with the lines goes here.
                    standard format for lines is a dictionary like so:
                    game = {
                        "home_team": home team's short name, 
                        "away_team": away team's short name,
                        "game_time": game time (miiiiight not be standardized), 
                        "home_line": home team's line, 
                        "away_line": away team's line,
                        "sport": name of the sport
                    }

                    right now the below code just stores and compares lines
                    using mysql
                    """

                    game["site"] = site

                    game_id = self.bets_DB.get_game_id(game)
                    self.bets_DB.add_moneyline(game,game_id)

                    betting_result = self.compare_moneylines(game_id,game)

                    if betting_result:
                        results.append(betting_result)

                    """
                    end of area where you put your code
                    """

            # if results:
            #     self.emailer.send_email(results)

            time_to_sleep = int(self.get_poisson_arrival_time(1/float(20*60)))
            print "sleeping {} seconds".format(time_to_sleep)
            self.countdown_sleep(time_to_sleep)

            if interrupted:
                try:
                    self.bets_DB.shutdown()
                    self.parser.shutdown()
                except:
                    pass

                break

    def countdown_sleep(self, time_to_sleep):
        for i in range(time_to_sleep):
            sys.stdout.write('\r')
            sys.stdout.write(str(time_to_sleep - i))
            sys.stdout.flush()
            time.sleep(1) 

            if interrupted:
                break

    def compare_moneylines(self, game_id, game):
        # Look at current line
        # determine if the underdog is the home team or the away team, same with favourite

        # find lines with winning differences
        # store line details
        # return the best difference

        result = None

        if game["home_line"] > game["away_line"]:
            # the home team is the underdog and the away team is the favourite
            favourite = "home"
            underdog = "away"

        else:
            underdog = "away"
            favourite = "home"

        # betting on a team with +320 for 100 bucks and a team with -250 for 280
        # then if the + team wins then you get +320 -280 = 40 and if - team wins you get 112 - 100 = 12

        money_lines_to_compare = self.bets_DB.get_moneylines(game)

        betting_max = {"now_team": None, "before_team": None, "date": None, "diff": 0}

        for money_line in money_lines_to_compare:
            gametime_string = self.convert_timestamp_to_time_string(money_line["poll_time"])
            
            if money_line[favourite + "_line"] + game[underdog + "_line"] > betting_max["diff"]:
                betting_max["diff"] = money_line[favourite + "_line"] + game[underdog + "_line"]
                betting_max["now_team"] = game[underdog+"_team"]
                betting_max["before_team"] = game[favourite+"_team"]
                betting_max["date"] = gametime_string

            elif money_line[underdog + "_line"] + game[favourite + "_line"] > betting_max["diff"]:

                betting_max["diff"] = money_line[underdog + "_line"] + game[favourite + "_line"]
                betting_max["now_team"] = game[favourite+"_team"]
                betting_max["before_team"] = game[underdog+"_team"]
                betting_max["date"] = gametime_string

        if betting_max["diff"] > 0:
            result = "We should have bet on {0} at {1} and {2} now for a difference of {3} points".format(
                betting_max["before_team"],betting_max["date"], betting_max["now_team"],betting_max["diff"])



        return result

    def flush_games(self):
        self.games = {"live": [], "upcoming": []}    

    def convert_game_time_to_timestamp(self, time):
        pass

    def convert_timestamp_to_time_string(self,timestamp):
        game_datetime = datetime.datetime.fromtimestamp(timestamp)
        game_string = str(game_datetime.day) + ":" + str(game_datetime.hour) + \
            ":" + str(game_datetime.minute) + " (Day:Hour:Minute)"

        return game_string

    def get_poisson_arrival_time(self, lambda_val):
        return 90
        #return -1*math.log(max(0.0001,random.random()))/float(lambda_val)

if __name__ == "__main__":
    odds = OddsComparer()

    def signal_handler(signal, frame):
        try:
            odd.bets_DB.shutdown()
            odds.parser.shutdown()
        except:
            pass

        global interrupted
        interrupted = True
        
    signal.signal(signal.SIGINT, signal_handler)

    interrupted = False

    odds.run()
    # odds.add_moneylines_to_database()
    # odds.flush_games()


