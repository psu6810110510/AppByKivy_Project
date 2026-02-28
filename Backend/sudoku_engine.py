#Backend/sudoku_engine.py

import random

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
    
    def _is_valid_col(self, board, col, num):
        # ตรวจสอบว่ามีตัวเลข num อยู่ในคอลัมน์ (col) นี้หรือไม่
        for i in range(9):
            if board[i][col] == num:
                return False
        return True
    
    def _is_valid_box(self, board, start_row, start_col, num):
        # ตรวจสอบว่ามีตัวเลข num อยู่ในกล่อง 3x3 หรือไม่
        for i in range(3):
            for j in range(3):
                if board[i + start_row][j + start_col] == num:
                    return False
        return True
    
    def is_safe(self, board, row, col, num):
        # หาจุดเริ่มต้นของกล่อง 3x3 ที่ช่อง (row, col) อาศัยอยู่
        box_start_row = row - row % 3
        box_start_col = col - col % 3
        
        # ต้องปลอดภัยทั้ง แถว, คอลัมน์ และ กล่อง 3x3
        return (self._is_valid_row(board, row, num) and
                self._is_valid_col(board, col, num) and
                self._is_valid_box(board, box_start_row, box_start_col, num))
    
    def find_empty_location(self, board):
        """
        ค้นหาช่องว่างในกระดาน (ช่องที่มีค่า 0)
        คืนค่า: (row, col) ถ้าเจอ, หรือ None ถ้ากระดานเต็มแล้ว
        """
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0:
                    return i, j
        return None
    
    def solve_sudoku(self, board):
        """
        แกปริศนา Sudoku โดยใช้ Backtracking Algorithm
        คืนค่า: True ถ้าแก้ได้สำเร็จ, False ถ้าไม่มีทางแก้
        """
        # 1. หาช่องว่าง ถ้าไม่เจอแปลว่าเต็มแล้ว (จบงาน)
        empty_loc = self.find_empty_location(board)
        if not empty_loc:
            return True # แก้เสร็จแล้ว!
        
        row, col = empty_loc

        # 2. ลองเติมเลข 1-9
        for num in range(1, 10):
            # ตรวจสอบว่าปลอดภัยไหมที่จะวางเลขนี้ (ใช้ฟังก์ชัน Day 1)
            if self.is_safe(board, row, col, num):
                board[row][col] = num # ลองวางดู

                # 3. วางแล้วลองไปแก้ช่องถัดไป (Recursive)
                if self.solve_sudoku(board):
                    return True

                # 4. ถ้าไปต่อไม่ได้ (ทางตัน) ให้ลบออก (Backtrack) แล้วลองเลขใหม่
                board[row][col] = 0

        return False # ลองครบ 1-9 แล้วไม่ได้เลย แปลว่าทางนี้ผิด
    
    def _fill_3x3_box(self, board, start_row, start_col):
        """สุ่มเติมเลข 1-9 ลงในกล่อง 3x3"""
        nums = list(range(1, 10))
        random.shuffle(nums) # สุ่มลำดับตัวเลข
        
        for i in range(3):
            for j in range(3):
                board[start_row + i][start_col + j] = nums.pop()

    def _fill_diagonal(self, board):
        """เติมเลขในกล่องแนวทแยง 3 กล่อง (กล่อง 0, 4, 8)"""
        for i in range(0, 9, 3):
            self._fill_3x3_box(board, i, i)

    def generate_board(self):
        """
        สร้างกระดาน Sudoku ที่สมบูรณ์และถูกต้องตามกฎ
        1. ล้างกระดาน
        2. สุ่มเติมแนวทแยง
        3. ใช้ Solver เติมส่วนที่เหลือ
        """
        # ล้างกระดานให้เป็น 0 ทั้งหมดก่อน
        self.board = [[0 for _ in range(9)] for _ in range(9)]
        
        # ขั้นตอนที่ 1: สุ่มเติมกล่องแนวทแยง (เพื่อให้ได้โจทย์ที่ไม่ซ้ำเดิม)
        self._fill_diagonal(self.board)
        
        # ขั้นตอนที่ 2: ใช้ Solver เติมช่องที่เหลือให้เต็ม
        self.solve_sudoku(self.board)
        
        return self.board


if __name__ == "__main__":
    game = SudokuEngine()
    print("Generating a new board...")
    board = game.generate_board()
    game.print_board()
    print("\nIs board valid?", "Yes" if game.solve_sudoku(board) else "No (Wait, it should be full already)")