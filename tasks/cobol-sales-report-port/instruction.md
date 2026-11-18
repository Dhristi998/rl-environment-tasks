# Port a COBOL control-break report to Python

`/app/legacy/salesrpt.cbl` is a GnuCOBOL batch program. It reads the
fixed-width file `sales.dat` from the current directory and prints a sales
report to standard output.

Write `/app/salesrpt.py`, a Python 3 program that, when run from a directory
containing a `sales.dat` file, prints **exactly** the same output as the COBOL
program, byte for byte, for any valid input file.

- Use only the Python standard library.
- Your program must not call `cobc` or any compiled COBOL program.
- GnuCOBOL (`cobc`) is installed so you can run the original and compare.
