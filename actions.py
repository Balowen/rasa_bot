from typing import Any, Text, Dict, List, Optional, Tuple, Union

from rasa_sdk import Action, Tracker
from rasa_sdk.forms import FormAction, REQUESTED_SLOT, logger
from rasa_sdk.events import AllSlotsReset, EventType, SlotSet
from rasa_sdk.executor import CollectingDispatcher

from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.types import Integer, TEXT
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.automap import automap_base

engine = create_engine("sqlite:///study_fields.db", echo=True)

Base = automap_base()
Session = sessionmaker(bind=engine)


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('categories.id'))
    data = Column(TEXT())
    children = relationship('Category',
                            backref=backref('parent', remote_side=[id]))

    def __repr__(self):
        return "TreeNode(data=%r, id=%r, parent_id=%r)" % (
            self.data,
            self.id,
            self.parent_id
        )


Base.prepare(engine, reflect=True)

StudyFields = Base.classes.study_fields


def _get_study_fields_names() -> List:
    """get study fields from db"""
    session = Session()
    study_fields_tuples = session.query(StudyFields.name).distinct()
    study_fields_list = [x[0] for x in study_fields_tuples]
    session.close()
    print(study_fields_list)
    return study_fields_list


def _get_limit_of_students(study_field, study_cycle, form_of_study) -> int:
    session = Session()
    limit_of_students = session.query(StudyFields.limit_of_students).filter_by(name=study_field,
                                                                               cycle=study_cycle,
                                                                               form_of_study=form_of_study
                                                                               ).first()
    return limit_of_students[0]


def _get_possible_study_forms(study_field_name: Text, study_cycle: Text) -> List:
    session = Session()
    study_forms_tuples = session.query(StudyFields.form_of_study).filter_by(name=study_field_name,
                                                                            cycle=study_cycle).distinct()
    study_forms_list = [x[0] for x in study_forms_tuples]
    session.close()
    return study_forms_list


def _get_study_cycles(study_field_name: Text) -> List:
    """get cycles of study for specific field of study"""
    session = Session()
    study_cycles_tuples = session.query(StudyFields.cycle).filter_by(name=study_field_name).distinct()
    study_cycles_list = [x[0] for x in study_cycles_tuples]
    session.close()
    return study_cycles_list


def _get_study_cycles_buttons(study_field_name: Text) -> Tuple[List, List]:
    study_cycles_list = _get_study_cycles(study_field_name)
    buttons = []
    for cycle in study_cycles_list:
        study_cycle = cycle
        payload = "/inform{\"study_cycle\": \"" + study_cycle + "\"}"

        buttons.append(
            {"title": f"{study_cycle.title()}",
             "payload": payload})
    return buttons, study_cycles_list


class ShowCategories(Action):
    """This action retrieves categories from db and displays them as buttons
        when user chooses endnode category, it returns appropriate utter_temple response"""
    def name(self) -> Text:
        return "show_categories"

    def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # categories
        current_category_level = tracker.get_slot("category_parent_id")
        session = Session()
        categories = session.query(Category).filter(Category.parent_id == current_category_level).all()
        session.close()

        # TODO add button list and update it according to current_category_level slot
        for category in categories:
            print(category.data)
        return []


class ShowFieldsOfStudies(Action):
    """This action retrieves pizza types (later from the db) and displays
    it to the user"""

    def name(self) -> Text:
        return "show_study_fields"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        study_fields = _get_study_fields_names()
        dispatcher.utter_message("Lista kierunków do wyboru: \n-" + "\n-".join(study_fields))

        return []


class ShowStudentsLimitForm(FormAction):
    """Form action to fill all slots required to show limits of students"""

    def name(self) -> Text:
        return "students_limit_form"

    @staticmethod
    def required_slots(tracker: "Tracker") -> List[Text]:
        """A list of required slots the form has to fill"""

        required_slot = ["study_field", "study_cycle", "form_of_study"]
        return required_slot

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict[Text, Any]]]]:

        return {"study_field": self.from_entity(entity="study_field",
                                                intent=["inform",
                                                        "show_limit_of_students"]),
                "study_cycle": self.from_entity(entity="study_cycle",
                                                intent=["inform",
                                                        "show_limit_of_students"]),
                "form_of_study": self.from_entity(entity="form_of_study",
                                                  intent=["inform",
                                                          "show_limit_of_students"])}

    def request_next_slot(
            self,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: Dict[Text, Any],
    ) -> Optional[List[EventType]]:
        for slot in self.required_slots(tracker):
            if self._should_request_slot(tracker, slot):
                if slot == "study_cycle":
                    study_field = tracker.get_slot("study_field")
                    buttons_list, cycles_values_list = _get_study_cycles_buttons(study_field)
                    if len(cycles_values_list) == 1:
                        cycle = cycles_values_list[0]

                        dispatcher.utter_message(f"Jedyny możliwy stopień studiów to: stopień {cycle} "
                                                 f"(wybrano automatycznie)")
                        return [SlotSet("study_cycle", cycle)]
                    else:
                        dispatcher.utter_button_message(text="Wybierz stopień studiów:", buttons=buttons_list)
                        return [SlotSet("study_cycle", slot)]
                elif slot == "form_of_study":
                    study_field = tracker.get_slot("study_field")
                    study_cycle = tracker.get_slot("study_cycle")
                    # Ask for form of study or auto_fill it if there is only one option
                    forms_of_study = _get_possible_study_forms(study_field, study_cycle)
                    print(len(forms_of_study))
                    if len(forms_of_study) == 1:
                        return [SlotSet("form_of_study", forms_of_study[0])]
                    else:
                        dispatcher.utter_message(template="utter_ask_form_of_study")
                        return [SlotSet("form_of_study", slot)]
                else:
                    # For all other slots, continue as usual
                    print(slot)
                    logger.debug(f"Request next slot '{slot}'")
                    dispatcher.utter_message(
                        template=f"utter_ask_{slot}", **tracker.slots
                    )
                    return [SlotSet(REQUESTED_SLOT, slot)]

        return None

    def submit(
            self,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Once required slots are filled, print message with slots values"""

        study_field = tracker.get_slot("study_field")
        study_cycle = tracker.get_slot("study_cycle")
        form_of_study = tracker.get_slot("form_of_study")

        limit = _get_limit_of_students(study_field, study_cycle, form_of_study)

        dispatcher.utter_message(f"Limit studentow na kierunku {study_field}, stopień {study_cycle} {form_of_study} "
                                 f"wynosi {limit}")
        return [AllSlotsReset()]
