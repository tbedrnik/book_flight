"""
Console application for flight booking using Kiwi.com APIs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Task: https://engeto.online/study/lesson/_wl9/unit/_36ZR
"""

import datetime
import argparse
# See: http://docs.python-requests.org/en/master/
import requests
import json


def ymdate(string):
    r"""Returns date object if parsed date is in future, otherwise raises error

    :param string: String of date in format YYYY-MM-DD
    :return: :class:`datetime <datetime>` object
    :rtype: datetime.datetime
    """
    try:
        date = datetime.datetime.strptime(string,"%Y-%m-%d")
        today = datetime.datetime.today()
        today = today.replace(hour=0,minute=0,second=0)
        if(date >= today):
            return date
        else:
            raise argparse.ArgumentTypeError("%s is not future date" % string)
    except ValueError:
        raise argparse.ArgumentTypeError("%s is not valid date" % string)


def iata(code):
    r"""Checks if provided string is 3 chars long

    :param code: IATA code
    :return: string uppercase
    """
    if len(code) == 3:
        return code.upper()
    else:
        raise argparse.ArgumentTypeError("%s is not valid IATA code" % code)


class Flight:

    def __init__(self, date, flyFrom, to, nightsOfStay, sort, bags, currency="CZK"):

        #: Date of departure in string formatted so API will take it
        self.date = str(date.day)+"/"+str(date.month)+"/"+str(date.year)

        #: IATA code of departure destination
        self.flyFrom = flyFrom

        #: IATA code of arrival destination
        self.to = to

        #: Nights to spend there before flying back
        self.daysInDestinationFrom = str(0)
        self.daysInDestinationTo = str(0)

        #: Oneway or round trip (default is oneway)
        self.typeFlight = "oneway"
        if nightsOfStay != None and nightsOfStay >= 0:
            self.typeFlight = "round"
            self.daysInDestinationFrom = str(nightsOfStay)
            self.daysInDestinationTo = str(nightsOfStay)

        #: Cheapest or fastest trip (default is cheapest)
        self.sort = "price"
        if sort != None:
            self.sort = sort

        #: Number of luggage
        self.bags = bags

        #: Currency
        self.currency = currency


    def getBookingToken(self):

        #: URL of flight search API + parameters
        url = "http://api.skypicker.com/flights"
        url += "?dateFrom="+self.date
        url += "&dateTo="+self.date
        url += "&flyFrom="+self.flyFrom
        url += "&to="+self.to
        url += "&typeFlight="+self.typeFlight
        url += "&daysInDestinationFrom="+self.daysInDestinationFrom
        url += "&daysInDestinationTo="+self.daysInDestinationTo
        url += "&sort="+self.sort
        url += "&limit=1"

        # Opening GET request
        r = requests.get(url)

        # If everything goes well
        if r.status_code == requests.codes.ok:
            # Parse JSON from response text
            data = json.JSONDecoder().decode(r.text)
            # If flight was found
            if data["_results"] > 0:
                #: Booking token
                self.token = data["data"][0]["booking_token"]
                return True
        return False

    def setPassenger(self, passenger):
        #: Passenger info
        #: :class: Passenger
        self.passenger = passenger

    def book(self):

        # URL of booking API
        url = "http://128.199.48.38:8080/booking"

        # Data requested by booking API
        data = {"booking_token": self.token,
             "passengers": {
                 "title": self.passenger.title,
                 "firstName": self.passenger.firstName,
                 "lastName": self.passenger.lastName,
                 "birthday": self.passenger.birthday,
                 "email": self.passenger.email,
                 "documentID": self.passenger.documentID
             },
             "currency": self.currency,
             "bags": self.bags}

        # Data must be JSON
        headers = {"content-type": "application/json"}

        # Opening POST request, converting data to JSON
        r = requests.post(url, data=json.dumps(data), headers=headers)

        # If everything goes well
        if r.status_code == requests.codes.ok:
            # Parse JSON from response text
            rsp = json.JSONDecoder().decode(r.text)
            # If reservation is confirmed
            if rsp["status"] == "confirmed":
                # Set reservation number
                self.pnr = rsp["pnr"]
                return True
        return False


class Passenger:
    def __init__(self, title, firstName, lastName, birthday, email, documentID):
        # Title Mr or Mrs - case sensitive, has to be capitalized
        self.title = str(title)
        self.firstName = str(firstName)
        self.lastName = str(lastName)
        #: String date format yyyy-mm-dd
        self.birthday = str(birthday)
        self.email = str(email)
        self.documentID = str(documentID)


args = argparse.ArgumentParser()

#: These 3 arguments are required
args.add_argument("--date", help="date of departure (format yyyy-mm-dd)", type=ymdate, required=True)
args.add_argument("--from", help="IATA code of departure destination", type=iata, dest="flyFrom", required=True)
args.add_argument("--to", help="IATA code of arrival destination", type=iata, required=True)

#: Optional arguments oneway (default) or return [number of nights]
args.add_argument("--one-way", dest="nights", help="Indicates one way trip", action="store_const", const=None)
args.add_argument("--return", dest="nights", help="Indicates round trip with nights of stay", default=0, type=int)

#: Optional arguments cheapest (default) or fastest
args.add_argument("--cheapest", dest="sort", help="Find cheapest flight", action="store_const", const="price")
args.add_argument("--fastest", dest="sort", help="Find shortest flight", action="store_const", const="duration")

#: Optional argument bags [number of bags] (default: 0)
args.add_argument("--bags", help="How many luggage?", type=int, default=0)

v = args.parse_args()

# Create new Flight
flight = Flight(v.date,v.flyFrom, v.to, v.nights, v.sort, v.bags)

# Set passenger
flight.setPassenger(Passenger("Mr","John","Doe","1969-12-03","john@doe.com","UK123456789"))

print("\nSearching flights...")
if flight.getBookingToken():
    print("Flight found!\n")
    print("Booking your flight...")
    if flight.book():
        print("Your reservation code is %s" % flight.pnr)
    else:
        print("Couldn't book flight")
else:
    print("Couldn't find flight")

