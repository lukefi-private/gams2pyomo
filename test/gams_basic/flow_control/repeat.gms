repeat ( 
    a = a + 1;
    display a;
until a = 5 );

repeat (
    a = a + 0.1;
    display a;
until abs(a-5) < 1e-6 );

repeat (
    a = a + 1;
    display a;
until a >= 3 );