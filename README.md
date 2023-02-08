# gams2pyomo: A Translator for Optimization Models

`gams2pyomo` is a utility tool aiming at translating GAMS files
automatically into Python/Pyomo code while preserving model structure.

The focus of this tool is around the building components of an optimization
model, i.e., **parameters, variables, constraints, and objectives**.
Although the GAMS language is flexible and powerful, this tool only provides
limited support for non-optimization components (e.g., `put` commands and dollar
control options).

## Installing

1. Install the package via `git clone`
2. Install required packages (see `requirements.txt`)

## Usage

Below is a simple example script for using the tool.
```python
# import the main class
from gams2pyomo import GAMSTranslator

# provide path for GAMS script
f = 'test/blend.gms'

# create an instance of the translator
gp = GAMSTranslator(f)

# translate the script
res = gp.translate()

# write the resulting pyomo script into a file
with open('result.py', 'w') as file:
    file.write(res)
```

## How it works
- The tool translates a GAMS model into a Pyomo model via a two-step procedure:

  1. The GAMS script is parsed into a parse-tree, where each statement is
  transformed into nodes on the tree based on GAMS grammar.
  2. The resulting nodes are then used to generate Pyomo code one by one.
- This tool is based on `Lark`, which is a parsing toolkit for Python.
The grammar of the GAMS language is inherited from [GAMS Parser](https://github.com/anderson-optimization/gams-parser).
- Ideally the program should be able to parse any legal GAMS programs and
selectively translate some parts of the script into Python/Pyomo.

## Tips for successful translation

This tool is still at an early development stage, and it is possible that the
execution fails at different stages (including parsing and transformation).
If you cannot manage to translate your GAMS code, the following tips may
be helpful.

1. Make sure that file is a legal GAMS file.
2. Many execution statements/dollar control options/suffices will not be
translated and can potentially cause errors. See the list of supported
statements below.
3. GAMS is case-insensitive, but please make sure the keywords in your GAMS code
follow certain rules. Typically the program is able to parse keywords in all
small cases, all capital cases, or camel Cases. But irregular ones (e.g., `bReAk`)
will not be identified.
### GAMS commands that will be translated with limitations
- `break`: argument will be omitted; will only break one loop

### GAMS commands that will not be translated
- function import
- `put`
- acronym definition

### Supported suffices
- 
### Supported dollar control options
- `$title`

## License
Distributed under the MIT License.

## Acknowledgements
This repo was forked from [GAMS parser](https://github.com/anderson-optimization/gams-parser),
whose grammar file (`gams.lark`) serves as an important basis for this project.
