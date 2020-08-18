# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/core/actions/#custom-actions/


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.forms import FormAction
from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk.executor import CollectingDispatcher

from sqlalchemy import create_engine, Table
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

PIZZA_TYPES = []
PIZZA_SIZES = ["duża", "średnia", "mała"]


Base = declarative_base()
engine = create_engine("sqlite:///menu_list.db", echo=True)


class PizzaList(Base):
    __table__ = Table('pizza_types', Base.metadata, autoload=True, autoload_with=engine)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def _update_menu_from_db():
    session = Session()
    menu = session.query(PizzaList.name).all()
    menu_list = [x[0] for x in menu]
    # print(formatted_menu)
    session.close()
    global PIZZA_TYPES
    PIZZA_TYPES = menu_list


def _validate_data(pizza_size: Text, pizza_sizes: List,
                   pizza_type: Text, pizza_types: List):
    """checks if values from slots are valid"""
    if pizza_size in pizza_sizes and pizza_type in pizza_types:
        results = {"pizza_size": pizza_size,
                   "pizza_type": pizza_type}
        return results
    return ""


class ShowPizzaTypes(Action):
    """This action retrieves pizza types (later from the db) and displays
    it to the user"""

    def name(self) -> Text:
        return "show_pizza_types"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        _update_menu_from_db()
        dispatcher.utter_message("Mamy nastepujace pizze w menu: \n-" + "\n-".join(PIZZA_TYPES))
        return []


class PizzaOrderForm(FormAction):
    """Form action to fill all slots required to make an order"""

    def name(self) -> Text:
        return "order_pizza_form"

    @staticmethod
    def required_slots(tracker: "Tracker") -> List[Text]:
        """A list of required slots the form has to fill"""

        return ["pizza_size", "pizza_type"]

    def submit(
            self,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Once required slots are filled, print message with slots values"""

        pizza_size = tracker.get_slot("pizza_size")
        pizza_type = tracker.get_slot("pizza_type")

        results = _validate_data(pizza_size, PIZZA_SIZES, pizza_type, PIZZA_TYPES)
        print(results)
        print(type(results))
        if len(results) == 0:
            dispatcher.utter_message(f"Pizza {results.get('pizza_type')} nie wchodzi w skład naszego menu")
            return []

        dispatcher.utter_message(f"Twoje zamówienie to {results.get('pizza_size')} pizza {results.get('pizza_type')}")
        return [AllSlotsReset()]
