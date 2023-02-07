put_utility 'ren' / 'test.dat';

put_utility 'log' / sysEnv.hello;

put_utility 'log' / '%gams.scrDir%';
put_utility 'log' / gams.scrDir;

put_utility 'exec' / 'touch ' i.tl:0 '.txt';

put_utility 'inc' / 'recall.txt' ;

put_utility 'incMsg' / 'recall.txt' ;

put_utility 'msg'    / 'This message is for the lst file.'
          / 'log'    / 'This message is for the log file.'
          / 'msgLog' / 'And this message is for the lst and the log file.' ;


put_utility 'gdxOut' / 'data' j.tl:0;

put_utility 'shell' / 'echo ' random:0:0 ' > ' j.tl:0;

put_utility 'click' / 'sets.html' ;

put_utility 'solver' / 'mip' / slv.tl:0;

put_utility 'assignText' / 'sym' / sym.te(sym) text;