# Adding a new dim test type

> When inventing a test name please specify it using the `snake_case` naming convention.

1. Run `make new-dim-test-type TEST_TYPE=[dim_test_type_name]` (`[dim_test_type_name]` needs to be replaced by what you want to call the test). This will create a couple of files:
    - `dim/models/dim_check_type/[dim_test_type_name].py`
    - `dim/models/dim_check_type/templates/[dim_test_type_name].sql.jinja`
1. Inside `dim/models/dim_check_type/[dim_test_type_name].py` Replace class name `REPLACE_ME` with `CamelCase` version of `[dim_test_type_name]` used with the first command and set the value of `DQ_CHECK_NAME` to be the same as `[dim_test_type_name]`.
1. Tweak `dim/models/dim_check_type/templates/[dim_test_type_name].sql.jinja to contain the desired SQL logic.
1. Inside `dim/const.py` add `"[dim_test_type_name]": getattr([dim_test_type_name], [dim_test_type_name:CamelCase]),` to the `TEST_CLASS_MAPPING` dictionary object.
1. Add tests for the new dim test under `tests/dim_checks/[dim_test_type_name]/[dim_test_type_name].py`
1. Add brief description and example of the new dim test type to the `dim/docs/dim_test_types.md` doc.
1. Add the test to your table's dim yaml config and have fun!
