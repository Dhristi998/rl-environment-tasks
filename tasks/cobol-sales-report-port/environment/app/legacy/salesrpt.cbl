       IDENTIFICATION DIVISION.
       PROGRAM-ID. SALESRPT.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT SALES-FILE ASSIGN TO "sales.dat"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD  SALES-FILE.
       01  SALES-REC.
           05 SR-REGION     PIC X(5).
           05 SR-AMOUNT     PIC 9(7)V99.
       WORKING-STORAGE SECTION.
       01  WS-EOF           PIC X VALUE "N".
       01  WS-PREV          PIC X(5) VALUE SPACES.
       01  WS-REG-TOT       PIC 9(9)V99 VALUE 0.
       01  WS-REG-CNT       PIC 9(5) VALUE 0.
       01  WS-GRAND         PIC 9(11)V99 VALUE 0.
       01  OUT-LINE.
           05 OL-REGION     PIC X(5).
           05 FILLER        PIC X(2) VALUE SPACES.
           05 OL-CNT        PIC ZZZZ9.
           05 FILLER        PIC X(2) VALUE SPACES.
           05 OL-AMT        PIC ZZZ,ZZZ,ZZ9.99.
       01  GRAND-LINE.
           05 FILLER        PIC X(14) VALUE "GRAND TOTAL".
           05 GL-AMT        PIC ZZ,ZZZ,ZZZ,ZZ9.99.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT SALES-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ SALES-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM PROCESS-REC
               END-READ
           END-PERFORM
           IF WS-PREV NOT = SPACES
               PERFORM PRINT-REGION
           END-IF
           MOVE WS-GRAND TO GL-AMT
           DISPLAY GRAND-LINE
           CLOSE SALES-FILE
           STOP RUN.
       PROCESS-REC.
           IF SR-REGION NOT = WS-PREV AND WS-PREV NOT = SPACES
               PERFORM PRINT-REGION
           END-IF
           MOVE SR-REGION TO WS-PREV
           ADD SR-AMOUNT TO WS-REG-TOT
           ADD 1 TO WS-REG-CNT
           ADD SR-AMOUNT TO WS-GRAND.
       PRINT-REGION.
           MOVE WS-PREV TO OL-REGION
           MOVE WS-REG-CNT TO OL-CNT
           MOVE WS-REG-TOT TO OL-AMT
           DISPLAY OUT-LINE
           MOVE 0 TO WS-REG-TOT
           MOVE 0 TO WS-REG-CNT.
