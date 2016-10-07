from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from config import CONFIG as config
from bs4 import BeautifulSoup
from pyvirtualdisplay import Display
from datetime import datetime
import time, json, re, math, string, sys


def print_json(json_object):
    print json.dumps(json_object, indent=4, sort_keys=True) 
    print "\n"

class bodog():

    def __init__(self, driver):
        self.driver = driver
        self.name = "bodog"
        self.links = config["sport_webpages"][self.name]
        self.class_print("initialized")

    def get_moneylines(self, sports):

        self.class_print("Obtaining moneylines")

        moneylines = []
        
        for sport in sports:

            self.class_print("Getting webpage for {}".format(sport))

            self.driver.get(self.links[sport])

            # scroll to make sure we reveal all the hidden games
            self.scroll()

            self.class_print("HTML obtained. Scraping site")
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            game_cells = soup.findAll("article", {"class" :"gameline-layout row ng-scope show-cta"})

            #print len(game_cells)
            
            for cell in game_cells:

                teams = cell.findAll("h3", {"class" :"ng-binding ng-scope"})
                away_team = translate_name(teams[0].getText(), sport)
                home_team = translate_name(teams[1].getText(), sport)
                if away_team=="unknown" or home_team=="unknown":
                    print "Team name not recognized. Skipping game ..."
                    continue

                day, gtime = re.split(' ',str(cell.findAll("time")[0].getText()))

                game_time = self.translate_datetime(day.strip(), gtime.strip())
                moneyline_cells = cell.findAll('ul', {'class': "ng-isolate-scope"})[1]
                lines = moneyline_cells.findAll('span', {'class': 'ng-binding'})

                # if no lines are listed, but game shows up on site
                if not lines:
                    away_line_string = str(-1)
                    home_line_string = str(-1)
                else:
                    away_line_string = str((lines[0].getText()))
                    home_line_string = str((lines[1].getText()))

                if "EVEN" in away_line_string:
                    away_line = 100
                else:
                    away_line = float(away_line_string)
                
                if "EVEN" in home_line_string:
                    home_line = 100
                else:
                    home_line = float(home_line_string)

                poll_time = int(time.time())

                moneylines.append(
                    {
                        "home_team": home_team, 
                        "away_team": away_team,
                        "game_time": game_time, 
                        "home_line": home_line, 
                        "away_line": away_line,
                        "poll_time": poll_time,
                        "sport":sport
                    }
                )

        return {"site": self.name, "moneylines": moneylines}

    def scroll(self):

        previous_length = 0
        first_scroll = True

        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            games = self.driver.find_elements_by_css_selector(
                'article.gameline-layout.ng-scope.show-cta')
            print "previous length was {0}, new length is {1}".format(
                previous_length, len(games))
            if (len(games) == previous_length) and (len(games) != 0 or not first_scroll):
                break
            previous_length = len(games)
            first_scroll = False
            time.sleep(0.5)

    # given day of the week and time of game, returns datetime in seconds fromtimestamp
    def translate_datetime(self, day, game_time):
        # get numeric value of game day and current day
        game_day = get_day_number(day)
        curr_day = int(time.strftime("%w"))
        # compute how many days in future the game is
        day_diff = (game_day-curr_day)%7
        # convert time to minute of day
        game_day_secs = self.time_to_sec(game_time)
        curr_day_secs = get_time_in_seconds()
        # compute how many seconds until the game
        seconds_til_game = 24*60*60*day_diff + game_day_secs-curr_day_secs
        # compute gametime in seconds fromtimestamp (with a bit of rounding)
        gametime_in_seconds = int(round((time.time()+seconds_til_game)/10)*10)
        return gametime_in_seconds

    def time_to_sec(self, game_time):
        
        parsed_time = game_time.split(":")
        ten_mins = int(parsed_time[1][0])
        one_mins = int(parsed_time[1][1])
        minutes = 10*ten_mins + one_mins
        am_pm = parsed_time[1][2]
        # bodog gives ET, so convert to PT
        hour = ((int(parsed_time[0])+12*(am_pm=="p"))-3)%24
        time_in_mins = 60*hour + minutes
        return 60*time_in_mins

    def class_print(self, string):
        print "{0}: {1}".format(self.name, string)





class FiveDimes():

    def __init__(self, driver):
        self.name = "FiveDimes"
        self.sports_translations = config["sports_translations"][self.name]
        self.driver = driver
        self.acceptable_delay = 10 #s

        self.class_print("initialized")

    def login(self):
        self.class_print("obtaining main webpage")

        self.driver.get('http://www.5dimes.eu/sportsbook.html')

        try:
            username = self.driver.find_element_by_name('customerID')
            password = self.driver.find_element_by_name('password')
        except:
            print "Cannot find login screen. May already be logged in - trying to continue..."
            return

        username.send_keys(config["passwords"]["FiveDimes"]["username"])
        password.send_keys(config["passwords"]["FiveDimes"]["password"])
        self.class_print("logging in")
        password.send_keys(Keys.RETURN)

    def logout(self):
        self.class_print("logging out")
        link = self.driver.find_element_by_link_text('sign out')
        link.click()

    def get_moneylines(self, sports):

        self.login()

        self.class_print("obtaining moneylines")

        moneylines = []

        for sport in sports:
            # print sport, sports
            if sport in self.sports_translations.keys():
                try:
                    # print self.sports_translations[sport]
                    WebDriverWait(self.driver, self.acceptable_delay).until(
                        EC.presence_of_element_located((By.NAME, self.sports_translations[sport])))
                        # self.driver.find_element_by_id(self.sports_translations[sport])))
                    # print "Page is ready!"
                except TimeoutException:
                    print "Loading took too much time!"

                # sleep(5)

                self.class_print("selecting {}".format(sport))
                # self.driver.find_element_by_name(self.sports_translations[sport]).click()
                try:
                    self.driver.find_element_by_name(self.sports_translations[sport]).click()
                    self.driver.find_element_by_id('btnContinue').click()
                except:
                    continue

                try:
                    # print self.sports_translations[sport]
                    WebDriverWait(self.driver, self.acceptable_delay).until(
                        EC.presence_of_element_located((By.ID, "tbl{}Game".format(config["tablenames"][sport]))))
                        # self.driver.find_element_by_id(self.sports_translations[sport])))
                    # print "Page is ready!"
                except TimeoutException:
                    print "Loading took too much time!"


                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                soup = soup.findAll("table", {"id": "tbl{}Game".format(config["tablenames"][sport])})[0]
                self.class_print("moneylines page loaded")
                self.class_print("obtaining moneylines")
                # print soup

                away_cells = soup.findAll("tr", { "class" : "linesRow" })
                home_cells = soup.findAll("tr", { "class" : "linesRowBot" })


                for i in range(len(away_cells)):

                    lines_for_this_game = {}

                    elements = away_cells[i].findAll('td')
                    
                    day = str(re.split(" ",elements[0].getText())[0]).upper()

                    away_list = re.split("\W+",elements[2].getText().replace(u'\xa0', u' '))[1:]
                    away_string = []
                    away_string.append(str(away_list[0]))
                    away_string.append(str(away_list[1]))
                    for j in range(2,len(away_list)):
                        if len(str(away_list[j])) > 2:
                            away_string.append(str(away_list[j]))
                        else:
                            break
                    
                    away_team = translate_name(" ".join(away_string), sport)
                    if away_team=="unknown":
                        print "Team name not recognized. Skipping game ..."
                        continue

                    if any(i.isdigit() for i in away_team) or ("Series" in away_team) or ("goes" in away_team):
                        continue

                    away_line = float(re.split(' ',str(elements[4].getText().replace(u'\xa0', u'')))[0])

                    elements = home_cells[i].findAll('td')

                    gtime = str(re.split(" ",elements[0].getText())[0]).lower()
                    game_time = self.translate_datetime(day.strip(), gtime.strip())
                    home_list = re.split("\W+",elements[2].getText().replace(u'\xa0', u' '))[1:]
                    home_string = []
                    home_string.append(str(home_list[0]))
                    home_string.append(str(home_list[1]))
                    for j in range(2,len(home_list)):
                        if len(str(home_list[j])) > 2:
                            home_string.append(str(home_list[j]))
                        else:
                            break
                    
                    home_team = translate_name(" ".join(home_string), sport)
                    if home_team=="unknown":
                        print "Team name not recognized. Skipping game ..."
                        continue

                    if any(i.isdigit() for i in home_team) or any(rem in home_team for rem in config["banned"]):
                        continue

                    home_line = float(re.split(' ',str(elements[4].getText().replace(u'\xa0', u'')))[0])

                    poll_time = int(time.time())

                    moneylines.append(
                        {
                            "home_team": home_team, 
                            "away_team": away_team,
                            "game_time": game_time, 
                            "home_line": home_line, 
                            "away_line": away_line,
                            "poll_time": poll_time,
                            "sport":sport
                        }
                    )
                    
                    #self.class_print("finished parsing {0} v {1}".format(home_team, away_team))
            else:
                self.class_print("{} not yet available".format(sport))

            self.class_print("finished parsing {}".format(sport))

            self.driver.execute_script("window.history.go(-1)")

            try:
                # print self.sports_translations[sport]
                WebDriverWait(self.driver, self.acceptable_delay).until(
                    EC.presence_of_element_located((By.NAME, self.sports_translations[sport])))
                    # self.driver.find_element_by_id(self.sports_translations[sport])))
                # print "Page is ready!"
            except TimeoutException:
                print "Loading took too much time!"

            self.driver.find_element_by_name(self.sports_translations[sport]).click() # unclick

        #try:
        #    self.logout()
        #except:
        #    pass

        return {"site": self.name, "moneylines": moneylines}

    # given day of the week and time of game, returns datetime in seconds fromtimestamp
    def translate_datetime(self, day, game_time):
        # get numeric value of game day and current day
        game_day = get_day_number(day)
        curr_day = int(time.strftime("%w"))
        # compute how many days in future the game is
        day_diff = (game_day-curr_day)%7
        # convert time to minute of day
        game_day_secs = self.time_to_sec(game_time)
        curr_day_secs = get_time_in_seconds()
        # compute how many seconds until the game
        seconds_til_game = 24*60*60*day_diff + game_day_secs-curr_day_secs
        # compute gametime in seconds fromtimestamp (with a bit of rounding)
        gametime_in_seconds = int(round((time.time()+seconds_til_game)/10)*10)
        return gametime_in_seconds

    def time_to_sec(self, game_time):
        
        parsed_time = game_time.split(":")
        ten_mins = int(parsed_time[1][0])
        one_mins = int(parsed_time[1][1])
        minutes = 10*ten_mins + one_mins
        am_pm = parsed_time[1][2]
        # bodog gives ET, so convert to PT
        hour = ((int(parsed_time[0])+12*(am_pm=="p"))-3)%24
        time_in_mins = 60*hour + minutes
        return 60*time_in_mins

    def class_print(self, string):
        print "{0}: {1}".format(self.name, string)





class Pinnacle():

    def __init__(self,driver):
        self.name = "Pinnacle"
        self.driver = driver
        self.links = config["sport_webpages"][self.name]
        self.class_print("initialized")
        self.acceptable_delay = 10 #s

    def login(self):

        self.class_print("obtaining main webpage")
        try:
            self.driver.get('https://www.pinnacle.com/en/rtn')

            try:
                loginScreen = self.driver.find_element_by_id('loginButton').click()
            except:
                print "Cannot find Login button. May already be logged in - trying to continue..."
                return

            username = self.driver.find_element_by_name('CustomerId')
            password = self.driver.find_element_by_name('Password')

            username.send_keys(config["passwords"]["Pinnacle"]["username"])
            password.send_keys(config["passwords"]["Pinnacle"]["password"])
            self.class_print("logging in")
            password.send_keys(Keys.RETURN)

        except TimeoutException:
            print "Loading took too much time! Trying again in one minute"
            # Go to different page in the meantime
            self.driver.get('https://www.google.ca')
            self.countdown_sleep(60) # sleep for 5 mins
            self.login()

    def logout(self):
        self.class_print("logging out")
        self.driver.find_element_by_link_text('Log Out').click()

    def get_moneylines(self, sports):

        self.login()

        self.class_print("Obtaining moneylines")

        moneylines = []
        
        for sport in sports:

            self.class_print("Getting webpage for {}".format(sport))

            try:
                self.driver.get(self.links[sport])

                WebDriverWait(self.driver, self.acceptable_delay).until(
                    EC.presence_of_element_located((By.ID, "LinesContainer")))
            except:
                print "Loading took too much time! Trying again in one minute"
                # Go to different page in the meantime
                self.driver.get('https://www.google.ca')
                self.countdown_sleep(60)

            time.sleep(0.5) # temp to make sure everything is loading
            self.class_print("HTML obtained. Scraping site")
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            days = soup.find_all("div", {'class':"linesDiv"})

            for day in days:
                
                betType = day.find("tr", {'class':"linesColumns"}).find("td").contents[0].strip()
                if betType != "Game":
                    continue

                semiGames = day.find_all("tr", {'class':re.compile("linesAlt*")}) #use regex to get linesAlt1 and linesAlt2

                teamCounter = 0
                flag = 0
                for cell in semiGames:
                    teamCounter += 1
                    # Check if flag indicating offline game is raised. If so, skip rest of game
                    if flag == 1:
                        flag = 0
                        continue

                    if teamCounter % 2 == 1:
                        away_team = cell.find("td", {"class":"teamId"}).find("span", {"class": "sTime"}).contents[0].strip()
                        away_team = translate_name(self.strip_unwanted_text(away_team),sport)
                        if away_team=="unknown":
                            print "Team name not recognized. Skipping game ..."
                            continue
                        day_info = cell.find("span", {"id": re.compile("gameProgress*")}).contents[0].strip()
                        d_info = day_info.split(" ")
                        day = str(d_info[0])
                        try:
                            away_line = float(cell.find("span", {"id": re.compile("divM*")}).string)
                        except:
                            print "Game with away team: ", away_team, " is offline or otherwise unavailable. Skipping game for now..."
                            flag = 1
                            continue
                    else:
                        home_team = cell.find("td", {"class":"teamId"}).find("span", {"class": "sTime"}).contents[0].strip()
                        home_team = translate_name(self.strip_unwanted_text(home_team),sport)
                        if home_team=="unknown":
                            print "Team name not recognized. Skipping game ..."
                            continue
                        gtime = str(cell.find("span", {"id": re.compile("gameProgress*")}).contents[0].strip())
                        try:
                            home_line = float(cell.find("span", {"id": re.compile("divM*")}).string)
                        except:
                            print "Game with home team: ", home_team, " is offline or otherwise unavailable. Skipping game for now..."
                            continue

                        game_time = self.translate_datetime(day.strip(), gtime.strip())
                        poll_time = int(time.time())
                        
                        moneylines.append(
                            {
                                "home_team": home_team, 
                                "away_team": away_team,
                                "game_time": game_time, 
                                "home_line": home_line, 
                                "away_line": away_line,
                                "poll_time": poll_time,
                                "sport":sport
                            }
                        )
        #try:
        #    self.logout()
        #except:
        #    pass

        return {"site": self.name, "moneylines": moneylines}

    def strip_unwanted_text(self,my_str):
        for item in config['to_strip']:
            # print "\'{0}\' in \'{1}\'? {2}".format(item, my_str, item in my_str)
            my_str = my_str.replace(item,'')

        return my_str

    def convert_decimal_to_american(self,decimal_odds):
        decimal_odds = float(decimal_odds)
        if decimal_odds >= 2:
            return int((decimal_odds - 1) * 100)
        elif decimal_odds < 2:
            return int(-100/(decimal_odds - 1))

    def time_zone_change(self, my_time):
        float_time = float(my_time) + 3
        return float_time

    # given day of the week and time of game, returns datetime in seconds fromtimestamp
    def translate_datetime(self, day, game_time):
        # get numeric value of game day and current day
        game_day = get_day_number(day)
        curr_day = int(time.strftime("%w"))
        # compute how many days in future the game is
        day_diff = (game_day-curr_day)%7
        # convert time to minute of day
        game_day_secs = self.time_to_sec(game_time)
        curr_day_secs = get_time_in_seconds()
        # compute how many seconds until the game
        seconds_til_game = 24*60*60*day_diff + game_day_secs-curr_day_secs
        # compute gametime in seconds fromtimestamp (with a bit of rounding)
        gametime_in_seconds = int(round((time.time()+seconds_til_game)/10)*10)
        return gametime_in_seconds

    def time_to_sec(self, game_time):
        
        parsed_time = game_time.split(":")
        ten_mins = int(parsed_time[1][0])
        one_mins = int(parsed_time[1][1])
        minutes = 10*ten_mins + one_mins
        am_pm = parsed_time[1][3]
        # bodog gives ET, so convert to PT
        hour = (int(parsed_time[0])+12*(am_pm=="P"))
        time_in_mins = 60*hour + minutes
        return 60*time_in_mins

    def countdown_sleep(self, time_to_sleep):
        for i in range(time_to_sleep):
            sys.stdout.write('\r')
            sys.stdout.write(str(time_to_sleep - i))
            sys.stdout.flush()
            time.sleep(1) 


        # if float_time >= 13:
        #     float_time -= 12
        #     if float_time >= 10:
        #         return "{0:5.2f}p".format(float_time)
        #     else:
        #         return "{0:4.2f}p".format(float_time)
        # elif float_time >= 12:
        #     return "{0:5.2f}p".format(float_time)
        # elif float_time < 1:
        #     return "{0:5.2f}a".format(float_time + 12)
        # elif float_time >= 10:
        #     return "{0:5.2f}a".format(float_time)
        # else:
        #     return "{0:4.2f}a".format(float_time)

    def class_print(self, string):
        print "{0}: {1}".format(self.name, string)



class SportsInteraction():

    def __init__(self,driver):
        self.name = "SportsInteraction"
        self.driver = driver
        self.links = config["sport_webpages"][self.name]
        self.class_print("initialized")
        self.acceptable_delay = 10 #s

    def login(self):
        self.class_print("obtaining main webpage")
        try:
            self.driver.get("https://www.sportsinteraction.com/")

            try:
                loginScreen = self.driver.find_element_by_id('headerLoginBtn').click()
            except:
                print "Cannot find Login button. May already be logged in - trying to continue..."
                return

            username = self.driver.find_element_by_id('iLoginUsername')
            password = self.driver.find_element_by_id('iLoginPassword')

            username.send_keys(config["passwords"]["SportsInteraction"]["username"])
            password.send_keys(config["passwords"]["SportsInteraction"]["password"])
            self.class_print("logging in")
            password.send_keys(Keys.RETURN)

        except:
            print "Loading took too much time! Trying again in one minute"
            # Go to different page in the meantime
            self.driver.get('https://www.google.ca')
            self.countdown_sleep(60) # sleep for 5 mins
            self.login()


    def logout(self):
        self.class_print("logging out")
        self.driver.find_element_by_id('headerLogoutBtn').click()

    def get_moneylines(self, sports):

        self.login()

        self.class_print("Obtaining moneylines")

        moneylines = []
        
        for sport in sports:

            if sport == "baseball_al" or sport == "baseball_nl":
                sport_name = "baseball"
            else:
                sport_name = sport

            self.class_print("Getting webpage for {}".format(sport))

            try:
                self.driver.get(self.links[sport])

                WebDriverWait(self.driver, self.acceptable_delay).until(
                    EC.presence_of_element_located((By.ID, "innerEventsWrapper")))
            except:
                print "Loading took too much time! Trying again in one minute"
                # Go to different page in the meantime
                self.driver.get('https://www.google.ca')
                self.countdown_sleep(60)

            time.sleep(0.5) # temp to make sure everything is loading
            self.class_print("HTML obtained. Scraping site")
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            games = soup.find_all("div", {'class':"game"})

            for game in games:
                
                temp_day = game.find("h2", {'class':"date"})
                if len(temp_day) > 0:
                    temp_day = temp_day.contents[0].split(",")
                    day = str(temp_day[0]).strip()

                try:
                    gtime = str(game.find("span", {'class':"time"}).contents[0]).strip()
                except:
                    print "Error when trying to obtain game time. Skipping game for now..."
                    continue

                game_time = self.translate_datetime(day, gtime)
                lines = game.findAll("ul", {'class':"runnerListRow twoWay"})[1]
                away_info = lines.findAll("li", {'class':"runner"})[0]
                home_info = lines.findAll("li", {'class':"runner"})[1]
                away_team = away_info.find("span", {'class':"name"}).contents[0]
                home_team = home_info.find("span", {'class':"name"}).contents[0]
                away_team = translate_name(str(away_team.split(':')[0]).strip(),sport_name)
                home_team = translate_name(str(home_team.split(':')[0]).strip(),sport_name)
                if away_team=="unknown" or home_team=="unknown":
                    print "Team name not recognized. Skipping game ..."
                    continue
                try:
                    away_line = float(away_info.find("span", {'class':"price"}).string)
                except:
                    print "Game with away team: ", home_team, " is offline or otherwise unavailable. Skipping game for now..."
                    continue
                try:    
                    home_line = float(home_info.find("span", {'class':"price"}).string)
                except:
                    print "Game with home team: ", home_team, " is offline or otherwise unavailable. Skipping game for now..."
                    continue

                poll_time = int(time.time())
                
                moneylines.append(
                    {
                        "home_team": home_team, 
                        "away_team": away_team,
                        "game_time": game_time, 
                        "home_line": home_line, 
                        "away_line": away_line,
                        "poll_time": poll_time,
                        "sport":sport_name
                    }
                )
        #try:
        #    self.logout()
        #except:
        #    pass

        return {"site": self.name, "moneylines": moneylines}

    def strip_unwanted_text(self,my_str):
        for item in config['to_strip']:
            # print "\'{0}\' in \'{1}\'? {2}".format(item, my_str, item in my_str)
            my_str = my_str.replace(item,'')

        return my_str

    # given day of the week and time of game, returns datetime in seconds fromtimestamp
    def translate_datetime(self, day, game_time):
        # get numeric value of game day and current day
        game_day = get_day_number(day)
        curr_day = int(time.strftime("%w"))
        # compute how many days in future the game is
        day_diff = (game_day-curr_day)%7
        # convert time to minute of day
        game_day_secs = self.time_to_sec(game_time)
        curr_day_secs = get_time_in_seconds()
        # compute how many seconds until the game
        seconds_til_game = 24*60*60*day_diff + game_day_secs-curr_day_secs
        # compute gametime in seconds fromtimestamp (with a bit of rounding)
        gametime_in_seconds = int(round((time.time()+seconds_til_game)/10)*10)
        return gametime_in_seconds

    def time_to_sec(self, game_time):
        
        parsed_time = game_time.split(":")
        ten_mins = int(parsed_time[1][0])
        one_mins = int(parsed_time[1][1])
        minutes = 10*ten_mins + one_mins
        # sportsinteraction uses 24h clock
        hour = int(parsed_time[0])
        time_in_mins = 60*hour + minutes
        return 60*time_in_mins

    def countdown_sleep(self, time_to_sleep):
        for i in range(time_to_sleep):
            sys.stdout.write('\r')
            sys.stdout.write(str(time_to_sleep - i))
            sys.stdout.flush()
            time.sleep(1) 


    def class_print(self, string):
        print "{0}: {1}".format(self.name, string)


def translate_name(long_form, sport):
    # print long_form
    for short_form in config["short_names"][sport]:
        if long_form in config["short_names"][sport][short_form]:
            return short_form

    return "unknown"


def get_day_number(day):

    if day in config["day_translations"]["sunday"]:
        return 0
    elif day in config["day_translations"]["monday"]:
        return 1
    elif day in config["day_translations"]["tuesday"]:
        return 2
    elif day in config["day_translations"]["wednesday"]:
        return 3
    elif day in config["day_translations"]["thursday"]:
        return 4
    elif day in config["day_translations"]["friday"]:
        return 5
    elif day in config["day_translations"]["saturday"]:
        return 6
    else:
        print "Invalid day name given as input."
        return -7

def get_time_in_seconds():
    currTime = str(datetime.now().time())
    parsedCurrTime = currTime.split(":")
    timeInSecs = 3600*int(parsedCurrTime[0])+60*int(parsedCurrTime[1])+float(parsedCurrTime[2])
    return timeInSecs



if __name__ == "__main__":
    display = Display(visible=0, size=(800, 600))
    display.start()
    driver = webdriver.Firefox()
    parser = Pinnacle(driver)
    sports = ['hockey', 'baseball']
    results = parser.get_moneylines(sports)

    # for result in results:
    #     if failure_string in results:
    #         print_json(result)
    print_json(results)

    driver.close()