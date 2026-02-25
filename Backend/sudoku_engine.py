class SudokuEngine:
    def __init__(self):
        # สร้างตาราง 9x9 โดยใส่ค่า 0 ไว้เป็นค่าเริ่มต้น (0 หมายถึงช่องว่าง)
        self.board = [[0 for _ in range(9)] for _ in range(9)]
        
    def print_board(self):
        # ฟังก์ชันแถมสำหรับปริ้นท์ดูหน้าตากระดานใน Console
        for row in self.board:
            print(row)
    
    def _is_valid_row(self, board, row, num):
        # ตรวจสอบว่ามีตัวเลข num อยู่ในแถว (row) นี้หรือไม่
        for i in range(9):
            if board[row][i] == num:
                return False
        return True