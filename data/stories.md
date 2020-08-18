## happy path
* greet
  - utter_greet
* menu
  - show_pizza_types
* inform{"pizza_type":"hawajska"}
  - order_pizza_form
  - form{"name":"order_pizza_form"}
  - form{"name":null}
* goodbye
 - utter_goodbye

## happy path 2
* order_pizza{"pizza_type":"wege", "pizza_size":"średnia"}
  - order_pizza_form
  - form{"name":"order_pizza_form"}
  - form{"name":null}
* goodbye
 - utter_goodbye
 
## say goodbye
* goodbye
  - utter_goodbye

