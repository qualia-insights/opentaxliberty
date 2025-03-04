# Open Tax Liberty

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

A FastAPI Python program that will complete your US based federal and Ohio
taxes for you. This software is open source software under the AGPLv3.  This
program is inspired by [Open Tax
Solver](https://opentaxsolver.sourceforge.net/forms.html) but with many
differences:
- Open Tax Liberty is written in Python
- Open Tax Liberty uses a json file for configuration

The software is still a work in progress.  

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

- [ ] complete the json config file for 1040
- [ ] complete the json config file for schedule A
- [ ] complete the json config file for schedule B
- [ ] complete the json config file for schedule C
- [ ] complete the json config file for schedule D
- [ ] complete the json config file for State of Ohio
- [ ] Integrate [jsonscheme](https://python-jsonschema.readthedocs.io/en/stable/)
    - this library should be able to validate our configuration files

## How to use curl to execute Open Tax Liberty

- curl can be used to execute the Open Tax Liberty with the command below

```bash
curl -v "http://mse-8:8000/api/process-tax-form"   -H "accept: application/json"   -H "Content-Type: multipart/form-data"   -F "config_file=@../bob_student_example.json"   -F "pdf_form=@/$HOME/code/taxes/2024/f1040_blank.pdf" --output /$HOME/temp/processed_form.pdf
```

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

### What this means:

- You can use, modify, and distribute this software freely.
- If you modify the software, you must make your modifications available under the same license.
- If you run a modified version of this software on a server that users interact with (for example, through a web interface), you must provide those users with access to the source code.
- There is no warranty for this program.

For the full license text, see the [LICENSE](LICENSE) file in this repository or visit [GNU AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.html).
