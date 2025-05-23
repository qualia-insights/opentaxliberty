# Open Tax Liberty

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

A FastAPI Python program that will complete your US based federal and Ohio
taxes for you. This software is open source software under the AGPLv3.  This
program is inspired by [Open Tax
Solver](https://opentaxsolver.sourceforge.net/forms.html) but with many
differences:
- Open Tax Liberty is written in Python
- Open Tax Liberty uses a json file for configuration

The software is still a work in progress it is not ready for prime time.   

## Tax Forms for 2024 Tax Year

Official Tax Forms with Instructions.  These forms are needed by Open Tax
Liberty to fill in the proper data.  The links below are provided for
convenience to the government sites.

**Tax Forms for 2024 Tax Year:**
* **US Fed 1040**: Main Form   [www.irs.gov/pub/irs-pdf/f1040.pdf](http://www.irs.gov/pub/irs-pdf/f1040.pdf),   [Instructions](http://www.irs.gov/pub/irs-pdf/i1040gi.pdf)
   * **Schedule A**: (Itemized Deductions)   [f1040sa.pdf](http://www.irs.gov/pub/irs-pdf/f1040sa.pdf),   [Instructions](http://www.irs.gov/pub/irs-pdf/i1040sca.pdf)
   * **Schedule B**: (Interest & Dividends)   [f1040sb.pdf](http://www.irs.gov/pub/irs-pdf/f1040sb.pdf)
   * **Schedule C**: (Business Taxes)   [f1040sc.pdf](http://www.irs.gov/pub/irs-pdf/f1040sc.pdf)
   * **Schedule D**: (Capital Gains/Losses)   [f1040sd.pdf](http://www.irs.gov/pub/irs-pdf/f1040sd.pdf)

## Todo

New strategy....I like having a single form in a single file so F1040.py should
be able to stand on its own.  It should validate, make the PDF, EVERYTHING 
related to a form F1040. Same goes for the W2. Then OpenTaxLiberty simply imports F1040
and asks F1040.py to make the PDF form.  OpenTaxLiberty will provide the OpenAPI
interfaces to the forms(s).  OpenTaxLiberty should have an OpenAPI call for each
tax form that it can process.

At some point we have to stop playing around and get our own taxes DONE :-)

- [ ] Eat own dog food
    - [ ] change F1040sc line h to a better name
- [X] pytests for F1040.py
- [X] pytests for F1040sc.py
- [ ] pytests for W2.py
- [ ] update the README.md in tests...how do we run all the tests? how do we run a single test
- [X] complete the json config file for schedule C
- [ ] schedule 1, this is where schedule C profit or loss goes, maybe ? we should look into this more
    - work on the validation of the first part of the form....we don't need a field for all yes/no do we?
- [ ] complete the json config file for State of Ohio
- [ ] complete the json config file for schedule A
- [ ] complete the json config file for schedule B
- [ ] complete the json config file for schedule D
- [ ] make a backup cron script that retrieves code from GitLab the pushes to code.rovitotv.org
    - this should work automatically so I don't have to worry about it
- [ ] Integrate some sort of jsonscheme
    - [pydantic](https://docs.pydantic.dev/latest/), this is used by FastAPI, we are using pydantic

## How to use curl to execute Open Tax Liberty

- curl can be used to execute the Open Tax Liberty with the command below

```bash
curl -v "http://mse-8:8000/api/process-tax-form"   -H "accept: application/json"   -H "Content-Type: multipart/form-data"   -F "config_file=@../bob_student_example.json"   -F "pdf_form=@/$HOME/code/taxes/2024/f1040_blank.pdf" --output /$HOME/temp/processed_form.pdf
```

## Is it W-2 or W2 or w2?

The official IRS form is called W-2 but Python doesn't apperciate the hypen.
Python considers the hypen a minus sign, To keep things simple we will use W2
_EVERYWHERE_. The name of this form has caused alot of pain for this effort
so we are going to simplify to W2.  

## Notes on OpenTaxSolver

- source file taxsolve_routines.c has a few functions of interest:
    - intercept_any_pdf_markups: 
    - exude_pdf_markups
    - grab_any_pdf_markupsa
- this location https://sourceforge.net/p/opentaxsolver/SrcCodeRepo/HEAD/tree/trunk/OTS_2024/src/formdata/OH_PIT_IT1040_meta.dat has meta data for OH IT1040 that looks useful

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

### What this means:

- You can use, modify, and distribute this software freely.
- If you modify the software, you must make your modifications available under the same license.
- If you run a modified version of this software on a server that users interact with (for example, through a web interface), you must provide those users with access to the source code.
- There is no warranty for this program.

For the full license text, see the [LICENSE](LICENSE) file in this repository or visit [GNU AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.html).
