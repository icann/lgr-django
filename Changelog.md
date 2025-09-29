# Changelog for lgr-django

## 7.0.0 (2025-09-25)

### Fixes
- Fix an issue in the codepoint view when deleting variants
- Fix a typo in the error message for leading hyphen in label validation
- Fix LGRDisplayView not being able to use the force_download parameter
- Fix the parent folder not being deleted when the last file in it is deleted
- Hide the "Label forms" button in the menu when the user is not logged in 

### Improvements
- Add more test coverage to the codebase
- Fix some tests that were failing
- Add stage to run the test suite in the Jenkinsfile pipeline
- Update Helm configuration
- Replace setup.py with pyproject.toml
- Upgrade Django to version 5.2
- Manage Python dependencies with pip-tools
- Remove Python 2 leftover code
- Remove Python support for versions 3.9 and older
- Update the base image used in containers/lgr-base with Red Hat UBI9 with Python 3.12
- Adjust ReadMe and License
- Make some changes to the codebase for Django compatibility
  - Add a new unmanaged class TemporaryLGRBase to replace a direct instance of the abstract class LGRBaseModel
  - Add new default Django setting DEFAULT_AUTO_FIELD
  - Prevent querysets from combining .distinct() and .delete()
  - Replace FileField using the widget ClearableFileInput with MultipleFileField for multi file uploads
  - Remove unused dependency django-redis-cache
  - Create a method is_ajax() in AjaxFormViewMixin to address the deprecation of request.is_ajax()
  - Replace the delete() method with form_valid() in BaseDeleteModelInitActiveMixin
  - Replace usage of the deprecated setting DEFAULT_FILE_STORAGE
  - Remove the deprecated setting USE_L10N
  - Replace positional arguments by keywords in save() calls
  - Move register_converter() calls into one place and remove registration duplication

## 6.1.2 (2024-09-08)
### New features
- Use Unicode version 15.1.0 by default

### Fixes
- Vulnerability fix: use POST for delete endpoints that were still GET

## 6.1.1 (2024-02-15)

### Improvements
- Always display codepoints list in label form
- Avoid exception when parsing IDNA invalid labels

### Fixes
- Fix codepoint view when the codepoint has variants

## 6.1.0 (2023-11-15)
### New features
- Add new IDNA 2008 compliance report tool

### Improvements
- Change label form output format
- Display reports expiration beside the reports
- Retry on IDN table download failure
- Label review:
  - only display an error on IDNA 2008 non-compliance
  - display A-label in another column

### Fixes
- Enable review for all IDN tables instead of a restricted set
- Stop failing for some exceptions in IDN table reviews
- Keep invalid code points in IDN table reviews
- Do not clean ICANN reports
- Correctly check IDNA 2008 compliance in label forms tool

## 6.0.0 (2023-08-04)
### New features
- Enable IDN review with RFC Core Requirements
- Allow processing a list of labels in the label form tool
- Allow editing of the reference LGR members
- Make reports expire
### Improvements
- Add IDN property in codepoint reports from IDN table reviews
- Remove cross-script tool
- Support any RFC format when importing an LGR
- Improve performances with iframes
- Add a better help text for label inputs
- Limit the file type choices for label files input
- Order reports and tasks with newest first
- Update help and about texts
- In validation mode, clicking a generated variant label will keep the same LGR selected
### Fixes
- Fix user create view
- Raise 404 on unexisting LGR
- Fix IDN table review LGR deletion
- Fix admin LGR automatic active selection
- Allow rz and ref LGR to have members with the same name under different common LGR
- Prevent open redirects


## 5.0.0 (2022-11-16)
### New features
- Add account for all users
- Add IDNA repertoires and MSRs management interfaces in admin
- Set fixed Unicode version
- Add a tasks information and management interface
- Add settings for variants computation limits in admin
- Allow unsupported code points to be displayed and edited in advanced tool
- Allow uploading reference LGR in IDN table review
- Add support for third-party authentication with JWT
- Compute label indexes for RZ LGR periodically for collision computation
### Improvements
- Remove email fields from forms as all users are logged in
- Improve user search and sorting in admin interface
- Stop sending emails upon tasks completion
- Make admin select default LGRs and only displays the default one in dropdowns
- Update some LGR selection dropdowns to include more LGR types
- Allow limiting the number of variants displayed in the validation tools
  - hide blocked variants above a certain limit
  - hide cross-scripts variants by default
- Add new general rules report in IDN tables review


## 4.0.0 (2021-04-27)
### New features
- Add IDN table review tools
- Add new interface to select between modes
### Improvements
- Reorganize Django apps and add new apps for IDN table review
- Rework all views to use class based views
- Ask for confirmation before removing reports
- Update Django to version 3.1.7
- Update dependencies versions
- Clean and update some assets
- Remove django-multiupload dependency

## 3.0.0 (2020-12-04)
### New features
- Add MSR-4 validating repertoire
- Add RZ-LGR validating repertoires
- Add RZ-LGR in built in LGRs list
- Allow collision tool to check collisions with existing set of TLDs downloaded from IANA
- Add a new basic mode:
  - new simplified interface
  - validate labels against RZ-LGR
  - allow checking for collisions as well
- Add language autocompletion from IANA language registry
- Stop support for python 2.7
### Improvements
- Update symetry report to consider contextual rules
- Update Django to version 2.2.1
- Update dependencies versions
- Handle internationalized email addresses
- Add translation to validation report
- Cache scripts and repertoires
- Improve memory consumption
- Display IDNA error as user friendly strings
- Correctly validate rule in LGR edition tool
### Fixes
- Fix memory leak
- Fix error handling in label validation

## 2.0.1 (2019-08-01)
### Improvements
- Mark out-of-script codepoints as warnings instead of errors (Fixes icann/lgr-core#15).

## 2.0.0 (2018-09-06)
### New features
- Support of Python 3. Compatibility with python2 is preserved for this release.
- Add MSR-3 validating repertoire.
- Create a "Tag" management page.
- Create a function to assign tags/WLE to code points.
- Allow choosing reference id when adding reference in editor.
- Add tags in code point list view.
### Improvements
- Improve display of LGR validation when rebuild is valid.
- Catch exceptions generated when input file is not a UTF-8 encoded file.
- Add required file encoding on label fields in forms.
- Update harmonization tool.
- When adding an out-of-repertoire variant, automatically add it to the repertoire + add the mapping to the code point.
- Improve wording of landing page.
- Improve handling of output for comparison tools for large LGRs.
- Update variant type to blocked for sample French LGR.
- Add notice that import function is permissive.
- Remove length limitation on label validation. Process will be run asynchronously if label can generate too many variants.
- Export testing of variant symmetry and transitivity in AJAX view.
- Add combined form of sequences in HTML output.
- Sort resource/repertoire file lists.
- Remove script parameter for harmonization tools.
- Display rule name(s) when a code point does not comply with a contextual rule.
- Better notification for invalid language tags.
- Better consistency on forms' labels.
### Fixes
- Fix redirection when adding a code point fails.
- Fix link to label in "Validate label" view.
- Remove references from repertoire on deletion.
- Replace number of variants by number of variant mappings in LGR validation statistics.
- Add proper error message when adding a tag to a sequence.
- Add support for missing language exception.
- Fix script retrievals from repertoires.
- Do not display useless error message when editing existing references.
- Fix creation of references from code point/variant edition screen.
- Fix deletion of action.
- Display code points in hexadecimal in HTML output.
- Add identity mapping for newly added variants not present in repertoire.
- Fix header hiding page content.
- Catch error in HTML output on ill-formed LGR's WLE.

## 1.9 (2017-03-09)
New features:
- New interface to view all forms of a label: display the U-label, A-label and code point sequence.
- Display the combined form of sequences.
- New tool to check that multiple LGRs are harmonized.
- New function to populate the missing symmetric and transitive variants.
- New function to add code point from a script.
- When adding a variant from another script, automatically add it to the repertoire if not present.
Fixes:
- Improve handling of large LGR.
- Fix variant type that could be be changed from "blocked".
- Fix label validation with ranges.
- Always display failed rule when validating a label.
- Improve display for summary (now renamed to LGR validation).
- Fix tag count in HTML output.
- Fix variant member count in HTML output.
- Use hyperlinks for the table of references in HTML output.
- Reduce number of rows in the variant set table in HTML output.
- Add number of mappings on variant set table in HTML output.
- Add link to save HTML output.

## 1.8.1 (2017-11-15)
Fixes:
 - Remove script/mimetype from merged description when all descriptions use the text/html mimetype.
 - Fix cross-script variants tool: output variants composed of code point which are in other scripts
   than the one(s) defined in the LGR.

## 1.8 (2017-10-18)
Fixes:
 - Merge LGR containing the same code point.
 - Improve HTML formatting for description in HTML output.
 - Improve merge for metadata's description element: if all descriptions are using HTML, then output will be in HTML.
 - Include references in WLE table in HTML output.
 - Better display of regex for WLE in HTML output.
 - Order metadata section per language then per script.
 - Fix size of variant set in HTML output.
 - Download result links are now ordered with newest on top.
 - Emphasize that the "Allocated set labels" file is optional.
 - Fix typo on homepage.
 - Update links to published RFC.
 - Allow import of an LGR part of a set as a standalone LGR.
 - Improve cross-script variants tool: generate the variants using the merged LGR,
   and list element LGRs used by the variants' code points.
 - Use redis as default Celery's broker for better stability.

## 1.7 (2017-06-26)
New features:
 - Handling of LGR sets: import multiple LGR documents to create a set (merged LGR).
 - Update difference and annotation tools to process LGR sets.
 - New tool to list cross-script variants for LGR sets.
 - HTML output of LGR: render LGR (or LGR set) in an HTML page.

Fixes:
 - Update dispositions to RFC: default for variants is "blocked", update default rules.
 - Improve design of homepage.
 - 500 error when clicking on a code point's variant that is not in LGR.
 - Fix Dockerfile: follow redirects for ICU downloads, add SHA-sum checks.

## 1.6 (2016-06-16)
Fixes:
 - Fix disposition handling in collision and diff tools
 - Improve tools error description provided in e-mail
 - Improve tools output
 - Manage bidirectional text in tools output
 - Improve tools performance

## 1.5 (2016-06-03)
New features:
 - Add cancel button on metadata screen                             
 - Add a list of current and imported LGRs into import/new panels         
 - Add supported Unicode version in about page  
 - Add an annotation tool
 - Add a checkbox to limit rules output in tools
 - Save tools output on server and display download link in session
 - Add a management command to clean storage
 - Some comparison leads to invalid LGR, return a download link for user to fix it

Fixes:
 - Fix manual import of RFC3743
 - Fix error field position in "Import CP from file" screen         
 - Improve code point details view
 - Various fixes in union and intersection
 - Various fixes in variant generation
 - Various display improvements
 - Limit logging output
 - Update RNG file
 - Various code factorization

## 1.4 (2016-04-27)
New features:
- Add documentation for core API and web-application global design.
- New tool for computing label collisions with two versions of an LGR.
  Add asynchronous interface for users to submit their requests
  and get result by email.

Fixes:
- Update RNG file to last version.
- Enable definition of when/not-when attribute on range.

## 1.3 (2016-03-02)
Fixes:
- Fix processing of look-around when anchor code point was repeated.
- Fix processing of infinite look-behind rules.
- Fix range expansion references.
- Correctly process variant label in context rule.
- Catch regex exceptions.
- Fix WLE validation.
- Handle empty set/pattern in WLE processing.
- Ensure label is in LGR when computing variants when dealing with sequences.
- When/Not-when attributes are mutually exclusive.
- Fix count attributes on char match operator.
- Fix class combinations for intersection and symetric-difference.
- Update RNG file.
- Make the title more clear to be clickable as « home »
- Correctly include Docker configuration.

## 1.2 (2016-02-05)
New features:
- WLE rules editor.
- Tag edition on code points.
- Context rules selection on code points.
- Expand ranges to single code point.
- New LGR comparison application:
	- Union of 2 LGRs.
	- Intersection of 2 LGRs.
	- Diff (text output) of 2 LGRs.
- Save summary to file.
- Delete LGR from working session.
- Add Dockerfile.
- Update namespace: imported LGRs will be converted to new namespace on export.

Fixes:
- Disable external entities when parsing XML (security review report).
- Properly handle IDNA errors in label validation.
- Import variants when manually importing from RFC file.
- Fix label variants generation when context rules are used.
