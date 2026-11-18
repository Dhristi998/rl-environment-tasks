# Port a legacy Fortran program to Python

`/app/legacy/amortize.f` is a Fortran 77 loan-amortisation program that a bank
still runs nightly. It reads loans from standard input and prints a repayment
schedule for each one.

Write `/app/amortize.py`, a Python 3 program that behaves **exactly** like the
Fortran program: same input format on stdin, byte-for-byte identical stdout,
for any valid input.

- Use only the Python standard library.
- Your program must not call the Fortran compiler or the legacy binary.
- A compiler (`gfortran`) is installed if you want to run the original and compare.
