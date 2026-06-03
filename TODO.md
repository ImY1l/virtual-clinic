# TODO - Fix failing E2E profile update test

- [ ] Update UI locators in `ui_tests/pages/profile_page.py` to match actual HTML field IDs/names from `ProfileForm` widgets (likely `id_phone`, `id_address`, etc.).
- [ ] Ensure profile update page is opened before attempting `update_profile()` (navigate/redirect handling).
- [ ] Run the failing test `pytest ui_tests/pages/test_registration_UI001.py::TestProfileUpdateE2E::test_profile_update_success -v -s`.
- [ ] If further failures occur, inspect returned page HTML and align locators/buttons.

