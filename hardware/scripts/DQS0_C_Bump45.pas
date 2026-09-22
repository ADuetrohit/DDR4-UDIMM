{ DQS0_C_Bump45.pas - replaces the square 0.331 mm bump on DQS0_C (net NetR10_1, layer L3) with the
  same extra length drawn with 45-degree chamfered corners (every corner 135 degrees).

  What it does, and nothing else:
    1. Removes every NetR10_1 track on L3 (Altium: Mid Layer 2) that lies inside the bump area
       x 10.27 ... 11.10 mm, y 10.19 ... 10.47 mm - i.e. the straight piece at y 10.200 and the
       square bump that DQS0_C_LengthFix.pas added (or the original straight piece if that was
       never run).
    2. Draws the piece again from (10.273, 10.200) to (11.095, 10.200) with a chamfered bump:
         (10.273,10.200) -> (10.370,10.200) -> (10.450,10.280) -> (10.450,10.379)
         -> (10.530,10.459) -> (10.770,10.459) -> (10.850,10.379) -> (10.850,10.280)
         -> (10.930,10.200) -> (11.095,10.200)
       Length over the bump 0.8905 mm instead of 0.560 mm straight: +0.331 mm, the same as before.
       It rises 0.259 mm, away from DQS0_T (0.2 mm below at y 10.000); nothing else is on L3 there.

  Run: open the PcbDoc > File > Run Script > Browse to DQS0_C_Bump45.PrjScr > FixDQS0C45 > OK.
  Undo with Ctrl+Z if needed. }

Var
    Board : IPCB_Board;

{ Board coordinate -> mm from the board origin }
Function MmX(C : TCoord) : Double;
Begin
    Result := CoordToMMs(C - Board.XOrigin);
End;

Function MmY(C : TCoord) : Double;
Begin
    Result := CoordToMMs(C - Board.YOrigin);
End;

{ True when (X, Y) in mm lies inside the bump area }
Function InBumpArea(X, Y : Double) : Boolean;
Begin
    Result := (X > 10.27) And (X < 11.10) And (Y > 10.19) And (Y < 10.47);
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

Procedure FixDQS0C45;
Var
    Iter   : IPCB_BoardIterator;
    T      : IPCB_Track;
    Net    : IPCB_Net;
    Old    : TInterfaceList;
    I      : Integer;
Begin
    Board := PCBServer.GetCurrentPCBBoard;
    If Board = Nil Then
    Begin
        ShowMessage('Open the DDR4 UDIMM PcbDoc first.');
        Exit;
    End;

    { 1. collect the NetR10_1 tracks on L3 that lie inside the bump area }
    Net := Nil;
    Old := TInterfaceList.Create;
    Iter := Board.BoardIterator_Create;
    Iter.AddFilter_ObjectSet(MkSet(eTrackObject));
    Iter.AddFilter_LayerSet(MkSet(eMidLayer2));
    Iter.AddFilter_Method(eProcessAll);
    T := Iter.FirstPCBObject;
    While T <> Nil Do
    Begin
        If (T.Net <> Nil) And (T.Net.Name = 'NetR10_1') Then
            If InBumpArea(MmX(T.X1), MmY(T.Y1)) And InBumpArea(MmX(T.X2), MmY(T.Y2)) Then
            Begin
                Old.Add(T);
                Net := T.Net;
            End;
        T := Iter.NextPCBObject;
    End;
    Board.BoardIterator_Destroy(Iter);

    If Old.Count = 0 Then
    Begin
        ShowMessage('No NetR10_1 track found in the bump area on L3. Nothing was changed.');
        Exit;
    End;

    { 2. remove them and draw the chamfered piece }
    PCBServer.PreProcess;
    For I := 0 To Old.Count - 1 Do
        Board.RemovePCBObject(Old.Items[I]);
    AddTrack(Net, 10.273, 10.200, 10.370, 10.200);
    AddTrack(Net, 10.370, 10.200, 10.450, 10.280);
    AddTrack(Net, 10.450, 10.280, 10.450, 10.379);
    AddTrack(Net, 10.450, 10.379, 10.530, 10.459);
    AddTrack(Net, 10.530, 10.459, 10.770, 10.459);
    AddTrack(Net, 10.770, 10.459, 10.850, 10.379);
    AddTrack(Net, 10.850, 10.379, 10.850, 10.280);
    AddTrack(Net, 10.850, 10.280, 10.930, 10.200);
    AddTrack(Net, 10.930, 10.200, 11.095, 10.200);
    PCBServer.PostProcess;
    Board.ViewManager_FullUpdate;
    ShowMessage('Replaced ' + IntToStr(Old.Count) + ' track(s) with the 45-degree bump (+0.331 mm). Save the PcbDoc.');
End;
