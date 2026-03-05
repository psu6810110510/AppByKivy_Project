# นำเข้าเครื่องมือของ Kivy ที่จำเป็นต้องใช้
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
import sys
import os

# ดึง path ของโฟลเดอร์หลัก เพื่อให้เรียกใช้ Backend ได้
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Backend.sudoku_engine import SudokuEngine

# สร้างคลาสสำหรับกระดาน Sudoku
class SudokuBoard(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 9       
        self.spacing = 2    
        self.padding = 10   
        self.cells = []  
        self.engine = SudokuEngine()

        # ตัวแปรป้องกันการคิดคะแนนตอนสร้างกระดาน
        self.is_generating = False 

        for i in range(81):
            cell = TextInput(
                text='',
                multiline=False,     
                halign='center',     
                font_size=24,
                input_filter='int'   
            )
            
            cell.cell_index = i                   
            cell.bind(text=self.check_answer)     
            
            self.add_widget(cell)
            self.cells.append(cell)

    # --- [แก้จุดนี้] นำระบบตรวจคำตอบและให้คะแนนมาใส่ ---
    def check_answer(self, instance, value):
        # ถ้ากำลังสร้างกระดาน หรือลบเป็นช่องว่าง ให้ข้ามไปเลย
        if self.is_generating or value == '':
            return
            
        # คำนวณหาแถว (row) และคอลัมน์ (col) จาก index
        row = instance.cell_index // 9
        col = instance.cell_index % 9
        num = int(value)

        # ถาม Backend ว่าเลขนี้ถูกไหม?
        is_correct = self.engine.check_move(row, col, num)
        
        # ดึงตัวแอปหลักมา เพื่อสั่งอัปเดตคะแนน
        app = App.get_running_app()

        if is_correct:
            instance.foreground_color = [0, 0.7, 0, 1]  # เปลี่ยนตัวอักษรเป็นสีเขียว
            instance.readonly = True                    # ตอบถูกแล้ว ล็อคช่องเลย
            app.update_score(100)                       # บวก 100 คะแนน
        else:
            instance.foreground_color = [1, 0, 0, 1]    # เปลี่ยนตัวอักษรเป็นสีแดง
            app.update_score(-20)                       # ตอบผิด หัก 20 คะแนน

    def clear_board(self, instance=None):
        self.is_generating = True  # เปิดโหมดป้องกัน

        for cell in self.cells:
            cell.text = ''
            cell.readonly = False
            cell.background_color = [1, 1, 1, 1]
            cell.foreground_color = [0, 0, 0, 1]  # [เพิ่ม] รีเซ็ตสีตัวอักษรกลับเป็นสีดำ
            
        self.engine.board = [[0 for _ in range(9)] for _ in range(9)]
        self.is_generating = False # ปิดโหมดป้องกัน

    def new_game(self, instance=None):
        self.clear_board()
        self.is_generating = True  # เปิดโหมดป้องกัน
        
        board_data = self.engine.generate_board("Easy")
        
        for i in range(81):
            row = i // 9
            col = i % 9
            val = board_data[row][col]
            
            cell = self.cells[i]
            if val != 0:
                cell.text = str(val)
                cell.readonly = True
                cell.background_color = [0.9, 0.9, 0.9, 1] 
                cell.foreground_color = [0, 0, 0, 1] # สีดำสำหรับเลขโจทย์
            else:
                cell.text = ''
                cell.readonly = False
                cell.background_color = [1, 1, 1, 1]    
                cell.foreground_color = [0, 0, 0, 1] # สีดำสำหรับช่องว่างเตรียมพิมพ์
                
        self.is_generating = False # ปิดโหมดป้องกัน


# กำหนดขนาดหน้าต่างแอปเริ่มต้น
Window.size = (500, 650)

# สร้างคลาสหลักของแอปพลิเคชัน
class SudokuApp(App):
    def build(self):
        main_layout = BoxLayout(orientation='vertical')

        self.seconds_elapsed = 0
        self.timer_event = None
        self.score = 0
        
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), padding=10)
        
        self.timer_label = Label(text="Time: 00:00", font_size=24, color=(1, 1, 1, 1))
        self.score_label = Label(text="Score: 0", font_size=24, color=(1, 1, 0, 1)) 
        
        top_bar.add_widget(self.timer_label)
        top_bar.add_widget(self.score_label)
        
        main_layout.add_widget(top_bar)

        self.board = SudokuBoard(size_hint=(1, 0.75))
        main_layout.add_widget(self.board)
        
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.15), padding=10, spacing=10)
        
        btn_new = Button(text="New Game", font_size=20)
        btn_clear = Button(text="Clear", font_size=20)
        btn_solve = Button(text="Solve", font_size=20)
        
        btn_new.bind(on_press=self.start_new_game)
        btn_clear.bind(on_press=self.clear_game)
        
        button_layout.add_widget(btn_new)
        button_layout.add_widget(btn_clear)
        button_layout.add_widget(btn_solve)
        
        main_layout.add_widget(button_layout)

        return main_layout

    def update_timer(self, dt):
        self.seconds_elapsed += 1
        minutes = self.seconds_elapsed // 60
        seconds = self.seconds_elapsed % 60
        self.timer_label.text = f"Time: {minutes:02d}:{seconds:02d}"

    def update_score(self, points):
        self.score += points
        self.score_label.text = f"Score: {self.score}"

    def start_new_game(self, instance):
        self.board.new_game()

        self.seconds_elapsed = 0
        self.timer_label.text = "Time: 00:00"

        self.score = 0
        self.score_label.text = "Score: 0"
        
        if self.timer_event:
            self.timer_event.cancel()

        self.timer_event = Clock.schedule_interval(self.update_timer, 1)

    def clear_game(self, instance):
        self.board.clear_board() 

        if self.timer_event:
            self.timer_event.cancel()

        self.score = 0
        self.score_label.text = "Score: 0"
            
        self.seconds_elapsed = 0
        self.timer_label.text = "Time: 00:00"
    
if __name__ == '__main__':
    SudokuApp().run()