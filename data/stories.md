## happy path
* greet
  - utter_greet
  - show_categories
* choose_category_level{"category_parent_id": 4}
  - show_categories
* fields_of_study
  - show_study_fields  
* show_limit_of_students{"study_field":"informatyka"}
  - students_limit_form
  - form{"name": "student_limit_form"}
  - form{"name": null}
  
## say goodbye
* goodbye
  - utter_goodbye

## out_of_scope
* out_of_scope
  - utter_out_of_scope
  - show_categories
