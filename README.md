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

Below is a simple example script for using the tool (at the root directory).
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

1. Make sure that file is a **legal GAMS file**.
2. Many **execution statements/dollar control options/suffices** will not be
translated and can potentially cause errors. See the list of supported
statements below.
3. Please end each statement with semicolon (`;`), even if it is the last one.
4. Please make sure that the spelling of keywords are regular (e.g., in all
small cases, all capital cases, or camel cases).
Although GAMS is case-insensitive, it is challenging to parse irregular keywords
(e.g., `bReAk`).
5. Please make sure that all the data definitions are clear and precise.
If the initial value of a parameter is not provided, then the tool will not
provide a default value (e.g., 0) to it (like GAMS does).
6. Avoid Python keywords in symbol names, e.g., `yield`.
7. Be careful with special characters in symbols which may have different
meanings in Python, e.g., dash (-), star (*), etc.

### GAMS commands that will not be translated
- function import
- `put` family
- acronym definition
- universal set (`*`)
- dynamic set
- end-of-line comments, in-line comments, outside margin comments, hidden comments

### GAMS commands that will be translated with limitations
- `table` definition: only basic formats of table definition is accepted for
now. Special formats, especially usage of tab, can lead to errors.
- `model` statement: limited ways of model definition are supported, including
  - `all`
  - list all equations
  - Moreover, the model declarations in GAMS and Pyomo are slightly
  different: in GAMS all models share the same scope for data and variables,
  whereas Pyomo models are independent of each other after cloning.
  This can also cause problems in some scenario.
- `alias`: there are only limited supports for alias lookup.
Complicated alias usage is not support. E.g.,
  ```gams
  alias(i, ip);
  darc(i, ip) = max(uarc(i, ip), uarc(ip, i));
  ```
- `break`: argument will be omitted; will only break one loop.


### Supported suffices
- `.l`
- `.lo`, `.up`, `.fx`
### Supported dollar control options
- `$title`

### Supported math functions
- `abs`, `ceil`, `floor`
- `log`, `log2`, `log10`
- trigonometric functions
- power functions and square root

## License
Distributed under the MIT License.

## Acknowledgements
This repo was forked from [GAMS parser](https://github.com/anderson-optimization/gams-parser),
whose grammar file (`gams.lark`) serves as an important basis for this project.
