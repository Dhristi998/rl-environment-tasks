      PROGRAM AMORT
C     LOAN AMORTISATION SCHEDULE
C     INPUT : ONE LOAN PER LINE -> PRINCIPAL  ANNUAL-RATE-PCT  MONTHS
C     OUTPUT: MONTH, INTEREST, PRINCIPAL, BALANCE, THEN A '----' LINE
      IMPLICIT NONE
      DOUBLE PRECISION P, RATE, R, PMT, XINT, PRIN, BAL
      INTEGER N, K, IOS
   10 READ(*,*,IOSTAT=IOS) P, RATE, N
      IF (IOS .NE. 0) GOTO 99
      R = RATE / 1200.0D0
      IF (R .EQ. 0.0D0) THEN
         PMT = P / N
      ELSE
         PMT = P * R / (1.0D0 - (1.0D0 + R)**(-N))
      END IF
      PMT = DNINT(PMT * 100.0D0) / 100.0D0
      BAL = P
      DO 20 K = 1, N
         XINT = DNINT(BAL * R * 100.0D0) / 100.0D0
         PRIN = PMT - XINT
         IF (K .EQ. N) PRIN = BAL
         BAL = BAL - PRIN
         WRITE(*,'(I4,3F12.2)') K, XINT, PRIN, BAL
   20 CONTINUE
      WRITE(*,'(A)') '----'
      GOTO 10
   99 STOP
      END
