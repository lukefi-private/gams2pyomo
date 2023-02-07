puthd out 'This header statement will be eliminated';

puthd 'Program Execution Date:', @26, system.date /
    'Source File:', @26, system.ifile /;

* Header Block with column headings for next page (will be used only if necessary)
puthd 'Table 1 (continued).  Plant Data and Results':0 /
      '-------------------'/;

puthd /'';