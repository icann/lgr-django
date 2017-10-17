# LGR-Toolset Release notes

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
