File factors /factors.dat/,
     results /results.dat/;
put factors;

put 'Transportation Model Factors' / /
    'Freight cost  ', f,
    @1#6, 'Plant capacity'/;

put @3, i.tl, @15, a(i)/;

put i.tl, @12, j.tl, @24, x.l(i,j):8:4 /;

put d(i):0:0 /;

put / 'Right Justified Comment':>50
    / 'Center Justified Truncated Comment':<>20;

put / / f:<6:2;