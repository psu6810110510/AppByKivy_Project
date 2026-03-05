#this is main.py, the main file of the project. It is responsible for running the app and managing the screens.
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
        # 1. ตั้งค่าตาราง: บังคับให้มี 9 คอลัมน์
        self.cols = 9       
        self.spacing = 2    # ระยะห่างระหว่างช่อง
        self.padding = 10   # ระยะขอบรอบกระดาน
        
        # 2. เตรียม List ว่างๆ เอาไว้เก็บช่องตัวเลขทั้ง 81 ช่อง
        self.cells = []  

        #สร้างตัวแปรสมองของเกม
        self.engine = SudokuEngine()

        # 3. วนลูป 81 รอบ เพื่อสร้างช่องกรอกตัวเลข (TextInput)
        for i in range(81):
            cell = TextInput(
                text='',
                multiline=False,     # ไม่ให้กด Enter ขึ้นบรรทัดใหม่
                halign='center',     # จัดตัวเลขให้อยู่ตรงกลาง
                font_size=24,
                input_filter='int'   # ให้กรอกได้เฉพาะตัวเลขเท่านั้น
            )
            # นำช่องที่สร้างเสร็จไปแปะบนกระดาน และเก็บเข้า List
            self.add_widget(cell)
            self.cells.append(cell)

    # ใส่ instance=None เพื่อไม่ให้แอปเด้งเวลาเรียกใช้งาน
    def clear_board(self, instance=None):
        # 1. ล้างตัวเลขบนหน้าจอให้ว่างเปล่า
        for cell in self.cells:
            cell.text = ''
            # รีเซ็ตสีและสถานะให้พิมพ์ได้ด้วย
            cell.readonly = False
            cell.background_color = [1, 1, 1, 1]
            
        # 2. ล้างข้อมูลในกระดานหลังบ้านให้เป็น 0 ทั้งหมด
        self.engine.board = [[0 for _ in range(9)] for _ in range(9)]

    # ใส่ instance=None เช่นกัน
    def new_game(self, instance=None):
        # เคลียร์กระดานเก่าทิ้งก่อน
        self.clear_board()
        
        # 1. ให้ Backend สร้างโจทย์ใหม่ (เริ่มต้นด้วยแบบ "Easy" ก่อน)
        board_data = self.engine.generate_board("Easy")
        
        # 2. นำตัวเลขจากโจทย์มาแสดงบนหน้าจอ
        for i in range(81):
            row = i // 9
            col = i % 9
            val = board_data[row][col]
            
            cell = self.cells[i]
            if val != 0:
                cell.text = str(val)
                # ถ้าเป็นตัวเลขโจทย์ (ล็อคไว้ไม่ให้แก้) และเปลี่ยนสีพื้นหลังให้เป็นสีเทาอ่อน
                cell.readonly = True
                cell.background_color = [0.9, 0.9, 0.9, 1] 
            else:
                cell.text = ''
                # ถ้าเป็นช่องว่าง (ให้ผู้เล่นพิมพ์ได้ปกติ) และเป็นสีขาว
                cell.readonly = False
                cell.background_color = [1, 1, 1, 1]    


# กำหนดขนาดหน้าต่างแอปเริ่มต้น
Window.size = (500, 650)

# สร้างคลาสหลักของแอปพลิเคชัน
class SudokuApp(App):
    def build(self):
        # 1. ต้องสร้าง Layout หลักขึ้นมาก่อนเป็นอันดับแรกสุดเลย
        main_layout = BoxLayout(orientation='vertical')

        self.seconds_elapsed = 0
        self.timer_event = None
        self.score = 0
        
        # --- [แก้จุดนี้ครับ] สร้างแถบด้านบน (Top Bar) จัดเรียงแนวนอน เพื่อใส่ 2 อย่าง ---
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), padding=10)
        
        self.timer_label = Label(text="Time: 00:00", font_size=24, color=(1, 1, 1, 1))
        self.score_label = Label(text="Score: 0", font_size=24, color=(1, 1, 0, 1)) # ให้คะแนนเป็นสีเหลือง
        
        # เอาเวลาและคะแนนใส่ในแถบด้านบน
        top_bar.add_widget(self.timer_label)
        top_bar.add_widget(self.score_label)
        
        # เอาแถบด้านบนไปแปะในหน้าจอหลัก
        main_layout.add_widget(top_bar)

        # ส่วนที่ 1: นำกระดาน SudokuBoard ที่เราสร้างไว้มาใส่ (ให้พื้นที่ความสูง 75%)
        self.board = SudokuBoard(size_hint=(1, 0.75))
        main_layout.add_widget(self.board)
        
        # ส่วนที่ 2: พื้นที่ปุ่มควบคุมด้านล่าง (ให้พื้นที่ความสูง 15%)
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.15), padding=10, spacing=10)
        
        btn_new = Button(text="New Game", font_size=20)
        btn_clear = Button(text="Clear", font_size=20)
        btn_solve = Button(text="Solve", font_size=20)
        
        # นำปุ่มมาผูกกับฟังก์ชันในคลาสนี้ เพื่อให้จัดการกระดานพร้อมกับเรื่องเวลาได้
        btn_new.bind(on_press=self.start_new_game)
        btn_clear.bind(on_press=self.clear_game)
        
        button_layout.add_widget(btn_new)
        button_layout.add_widget(btn_clear)
        button_layout.add_widget(btn_solve)
        
        main_layout.add_widget(button_layout)

        # คำสั่ง return ต้องอยู่ตรงนี้
        return main_layout

    def update_timer(self, dt):
        """อัปเดตเวลาบนหน้าจอทุกๆ 1 วินาที"""
        self.seconds_elapsed += 1
        minutes = self.seconds_elapsed // 60
        seconds = self.seconds_elapsed % 60
        self.timer_label.text = f"Time: {minutes:02d}:{seconds:02d}"
    
    def update_timer(self, dt):
        self.seconds_elapsed += 1
        minutes = self.seconds_elapsed // 60
        seconds = self.seconds_elapsed % 60
        self.timer_label.text = f"Time: {minutes:02d}:{seconds:02d}"

    def update_score(self, points):
        self.score += points
        self.score_label.text = f"Score: {self.score}"

    def start_new_game(self, instance):
        """กด New Game: สั่งสร้างโจทย์ และเริ่มจับเวลา"""
        self.board.new_game()

        # รีเซ็ตเวลาและเริ่มนับใหม่
        self.seconds_elapsed = 0
        self.timer_label.text = "Time: 00:00"

        self.score = 0
        self.score_label.text = "Score: 0"
        
        # ยกเลิกเวลาเก่าถ้ามี
        if self.timer_event:
            self.timer_event.cancel()

        self.timer_event = Clock.schedule_interval(self.update_timer, 1)

    def clear_game(self, instance):
        """กด Clear: ล้างกระดาน และหยุดเวลา"""
        self.board.clear_board() 

        # หยุดเวลาและรีเซ็ตกลับเป็น 0
        if self.timer_event:
            self.timer_event.cancel()

        self.score = 0
        self.score_label.text = "Score: 0"
            
        self.seconds_elapsed = 0
        self.timer_label.text = "Time: 00:00"
    
    
# คำสั่งสำหรับเริ่มรันโปรแกรม
if __name__ == '__main__':
    SudokuApp().run()