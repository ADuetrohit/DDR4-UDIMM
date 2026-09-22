{ DQS0_C_LengthFix.pas - adds 0.331 mm to DQS0_C (net NetR10_1, the DRAM side of R10) so it matches
  DQS0_T (NetR9_1) within the JEDEC 0.1 mm pair rule (main spec Table 11).

  What it does, and nothing else:
    1. Finds the one straight track of net NetR10_1 on layer L3 (Altium: Mid Layer 2) that runs
       horizontally from (10.273, 10.200) to (11.095, 10.200) mm.
    2. Removes it.
    3. Draws it again as 5 short tracks with a small upward bump in the middle:
         (10.273,10.200) -> (10.450,10.200) -> (10.450,10.3655) -> (10.850,10.3655)
                         -> (10.850,10.200) -> (11.095,10.200)
       The two 0.1655 mm uprights add 2 x 0.1655 = 0.331 mm. The bump goes up, away from
       DQS0_T (which runs 0.2 mm below at y 10.000); nothing else is on L3 in that spot.

  Run: open the PcbDoc > File > Run Script > Browse to DQS0_C_LengthFix.PrjScr > FixDQS0C > OK.
  Run it once only (a second run finds nothing to change and says so). Undo with Ctrl+Z if needed. }

Var
    Board : IPCB_Board;

{ True when two coordinates (in mm) are the same to within 0.02 mm }
Function IsClose(A, B : Double) : Boolean;
Begin
    Result := Abs(A - B) < 0.02;
End;

{ Board coordinate -> mm from the board origin }
Function MmX(C : TCoord) : Double;
Begin
    Result := CoordToMMs(C - Board.XOrigin);
End;

Function MmY(C : TCoord) : Double;
Begin
    Result := CoordToMMs(C - Board.YOrigin);
End;

{ Add one 0.1 mm track of the given net on L3 from (X1,Y1) to (X2,Y2) in mm }
Procedure AddTrack(Net : IPCB_Net; X1, Y1, X2, Y2 : Double);
Var
    T : IPCB_Track;
Begin
    T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
    T.Layer := eMidLayer2;                                   { L3_DQ_ADDR }
    T.Width := MMsToCoord(0.1);
    T.X1 := Board.XOrigin + MMsToCoord(X1);
    T.Y1 := Board.YOrigin + MMsToCoord(Y1);
    T.X2 := Board.XOrigin + MMsToCoord(X2);
    T.Y2 := Board.YOrigin + MMsToCoord(Y2);
    T.Net := Net;
    Board.AddPCBObject(T);
    PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, T.I_ObjectAddress);
End;

Procedure FixDQS0C;
Var
    Iter  : IPCB_BoardIterator;
    T     : IPCB_Track;
    Found : IPCB_Track;
    Net   : IPCB_Net;
    AX, AY, BX, BY : Double;
Begin
    Board := PCBServer.GetCurrentPCBBoard;
    If Board = Nil Then
    Begin
        ShowMessage('Open the DDR4 UDIMM PcbDoc first.');
        Exit;
    End;

    { 1. find the straight L3 piece of NetR10_1 between x 10.273 and 11.095 at y 10.200 }
    Found := Nil;
    Iter := Board.BoardIterator_Create;
    Iter.AddFilter_ObjectSet(MkSet(eTrackObject));
    Iter.AddFilter_LayerSet(MkSet(eMidLayer2));
    Iter.AddFilter_Method(eProcessAll);
    T := Iter.FirstPCBObject;
    While (T <> Nil) And (Found = Nil) Do
    Begin
        If (T.Net <> Nil) And (T.Net.Name = 'NetR10_1') Then
        Begin
            AX := MmX(T.X1); AY := MmY(T.Y1);
            BX := MmX(T.X2); BY := MmY(T.Y2);
            If (IsClose(AY, 10.2) And IsClose(BY, 10.2)) And
               ((IsClose(AX, 10.273) And IsClose(BX, 11.095)) Or (IsClose(AX, 11.095) And IsClose(BX, 10.273))) Then
                Found := T;
        End;
        T := Iter.NextPCBObject;
    End;
    Board.BoardIterator_Destroy(Iter);

    If Found = Nil Then
    Begin
        ShowMessage('Did not find the straight NetR10_1 piece on L3 at y 10.2 mm (already fixed, or the route changed). Nothing was changed.');
        Exit;
    End;

    { 2. remove it and 3. draw it back with the bump }
    PCBServer.PreProcess;
    Net := Found.Net;
    Board.RemovePCBObject(Found);
    AddTrack(Net, 10.273, 10.200, 10.450, 10.200);
    AddTrack(Net, 10.450, 10.200, 10.450, 10.3655);
    AddTrack(Net, 10.450, 10.3655, 10.850, 10.3655);
    AddTrack(Net, 10.850, 10.3655, 10.850, 10.200);
    AddTrack(Net, 10.850, 10.200, 11.095, 10.200);
    PCBServer.PostProcess;
    Board.ViewManager_FullUpdate;
    ShowMessage('DQS0_C lengthened by 0.331 mm (bump added on L3). Save the PcbDoc.');
End;
